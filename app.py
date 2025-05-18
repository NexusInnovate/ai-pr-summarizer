import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone, timedelta
from admin_dashboard import render_admin_tab
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from github_utils import fetch_prs, get_diff, fetch_org_repos, fetch_codeql_alerts
from ai_summarizer import summarize_diff, review_pr, summarize_all_prs
from metrics_utils import analyze_pr_metrics, add_pr_analytics

# Load environment variables and configure page
load_dotenv()
st.set_page_config(
    page_title="PR Review Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0066cc;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        font-weight: 500;
        color: #444;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f2f8ff;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        height: 100%;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0066cc;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .alert-critical {
        background-color: #ffeef0;
        border-left: 4px solid #d73a49;
    }
    .alert-high {
        background-color: #fff5ee;
        border-left: 4px solid #e36209;
    }
    .alert-medium {
        background-color: #fffbdd;
        border-left: 4px solid #dbab09;
    }
    .alert-low {
        background-color: #f0fff4;
        border-left: 4px solid #28a745;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #e6f0ff;
        border-bottom: 2px solid #0066cc;
    }
    .pr-summary {
        border-bottom: 1px solid #eee;
        padding-bottom: 1rem;
        margin-bottom: 1rem;
    }
    .small-text {
        font-size: 0.8rem;
        color: #666;
    }
    .tooltip {
        position: relative;
        display: inline-block;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'open_prs' not in st.session_state:
    st.session_state.open_prs = []
if 'merged_prs' not in st.session_state:
    st.session_state.merged_prs = []
if 'repo_summaries' not in st.session_state:
    st.session_state.repo_summaries = []
if 'metrics_df' not in st.session_state:
    st.session_state.metrics_df = None
if 'alerts' not in st.session_state:
    st.session_state.alerts = {}

# Sidebar for configuration
with st.sidebar:
    st.image("pr-ai-agent.png", width=150)
    st.markdown("## ⚙️ Configuration")
    
    # GitHub configuration
    st.markdown("### GitHub Settings")
    org = st.text_input("GitHub Organization", "NexusInnovate")
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        token = st.text_input("GitHub Token", type="password")
        if token:
            st.success("Token provided")
        else:
            st.warning("Please provide a GitHub token or set GITHUB_TOKEN environment variable")
    
    # Date range selection
    st.markdown("### Date Range")
    today = datetime.now()
    default_start = today - timedelta(days=30)
    col1, col2 = st.columns(2)
    with col1:
        since = st.date_input("Start Date", default_start)
    with col2:
        until = st.date_input("End Date", today)
    
    if since > until:
        st.warning("End date should be later or equal to start date")
    
    # Repository selection
    st.markdown("### Repositories")
    if org and token:
        with st.spinner("Fetching repositories..."):
            repo_names_list = fetch_org_repos(org, token)
        
        if repo_names_list:
            selected_repo_list = st.multiselect(
                f"Select repositories from {org}", 
                options=repo_names_list,
                help="Select one or more repositories to analyze"
            )
            if not selected_repo_list:
                st.info("Please select at least one repository")
        else:
            st.warning(f"No repositories found under {org}")
            selected_repo_list = []
    else:
        selected_repo_list = []
        st.info("Please provide GitHub organization and token")
    
    # Help section
    with st.expander("ℹ️ Help"):
        st.markdown("""
        **PR Review Assistant** helps you:
        - Summarize merged PRs using AI
        - Get AI-powered code reviews for open PRs
        - Analyze PR metrics and trends
        - Track security alerts
        
        To get started:
        1. Enter your GitHub organization
        2. Select repositories
        3. Choose a date range
        4. Use the tabs above to access different features
        """)

# Main content
st.markdown("<h1 class='main-header'>GitPulse AI Assistant</h1>", unsafe_allow_html=True)

if not org or not token or not selected_repo_list:
    st.info("👈 Please configure the required settings in the sidebar")
    
    st.markdown("""
    This tool provides:
    - **AI-powered PR summaries** - Get concise summaries of code changes
    - **Code quality reviews** - Receive feedback on open PRs
    - **PR metrics & analytics** - Track team performance with visual charts
    - **Security monitoring** - Stay on top of code security issues
    """)
    
    st.stop()

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📚 Merged PRs Summary",
    "👁️ Open PRs Review", 
    "📊 PR Metrics & Analytics", 
    "🛡️ Security Scans",
    "⚙️ Admin Metrics"
])

# ------------------- TAB 1: Merged PRs -------------------
with tab1:
    st.markdown("<h2 class='subheader'>Merged Pull Requests Summary</h2>", unsafe_allow_html=True)
    st.markdown("""
    Get AI-powered summaries of merged pull requests during the selected time period.
    This helps you keep track of what changes were made across your repositories.
    """)
    
    if st.button("Generate Merged PR Summaries", type="primary", use_container_width=True):
        all_merged_prs = []
        all_repos_summary = []
        
        for repo in selected_repo_list:
            with st.spinner(f"Fetching merged PRs for {repo}..."):
                prs = fetch_prs(repo, token, since.isoformat(), until.isoformat(), state="closed")
                
                if prs:
                    st.success(f"Found {len(prs)} merged PR(s) in {repo}")
                    
                    progress_bar = st.progress(0)
                    pr_data = []
                    repo_summaries = ""
                    for i, pr in enumerate(prs):
                        with st.spinner(f"Summarizing PR #{pr['number']}..."):
                            diff = get_diff(repo, pr['number'], token)
                            summary = summarize_diff(diff)
                            repo_summaries = repo_summaries+'\n'+summary
                            merged_date = datetime.strptime(pr['merged_at'], "%Y-%m-%dT%H:%M:%SZ") if pr.get('merged_at') else None
                            
                            # Only include if the PR was actually merged
                            if merged_date:
                                pr_info = {
                                    "Repository": repo,
                                    "PR Number": pr['number'],
                                    "Title": pr['title'],
                                    "Author": pr['user']['login'],
                                    "Merged At": merged_date,
                                    "URL": pr['html_url'],
                                    "Summary": summary,
                                    "Additions": pr.get('additions', 0),
                                    "Deletions": pr.get('deletions', 0)
                                }
                                pr_data.append(pr_info)
                        
                        # Update progress bar
                        progress_bar.progress((i + 1) / len(prs))

                    repo_summary = summarize_all_prs(repo_summaries)
                    if repo_summary:
                        repo_summary = {
                            "Repository": repo,
                            "summary":repo_summary
                        }
                    all_repos_summary.append(repo_summary)
                    all_merged_prs.extend(pr_data)
                else:
                    st.info(f"No merged PRs found for {repo} in the selected date range")
        
        st.session_state.merged_prs = all_merged_prs
        st.session_state.repo_summaries = all_repos_summary
    
    # Display Overall release notes
    if st.session_state.repo_summaries:
        st.markdown("## Overall Summary")
        df = pd.DataFrame(st.session_state.repo_summaries)
        # Render as Markdown table with wrapped columns
        for i, row in df.iterrows():
            st.markdown("---")
            cols = st.columns([1, 3])  # Adjust column widths
            cols[0].markdown(f"**{row['Repository']}**")
            cols[1].markdown(row['summary'], unsafe_allow_html=True)

    st.markdown('<hr style="border:1px solid #eee"/>', unsafe_allow_html=True)
    # Display merged PRs if available
    if st.session_state.merged_prs:
        st.markdown(f"## Merged PRs List")
        
        # Sort by merged date, newest first
        sorted_prs = sorted(st.session_state.merged_prs, key=lambda x: x['Merged At'], reverse=True)
        
        # Group by repository
        repos = list(set(pr['Repository'] for pr in sorted_prs))
        
        # Repository filter
        if len(repos) > 1:
            selected_repo = st.selectbox("Filter by Repository", ["All"] + repos)
        else:
            selected_repo = "All"
        
        # Filter PRs by repository if needed
        if selected_repo != "All":
            display_prs = [pr for pr in sorted_prs if pr['Repository'] == selected_repo]
        else:
            display_prs = sorted_prs
        
        # Display PRs as cards
        for pr in display_prs:
            summary_preview = ' '.join(pr['Summary'].split()[:10]) + "..."
            with st.expander(f"**#{pr['PR Number']} - {pr['Title']} | {pr['Repository']}]**"):
                with st.container():
                    # PR Header with metadata
                    st.markdown(f"**[#{pr['PR Number']} - {pr['Title']}]({pr['URL']})**")
                    st.markdown(f"Repository: **{pr['Repository']}** | Author: **{pr['Author']}** | Merged: **{pr['Merged At'].strftime('%Y-%m-%d %H:%M')}**")
                    st.markdown(f"{pr['Summary']}")
                    # Link to GitHub
                    st.markdown(f"[View on GitHub]({pr['URL']})", unsafe_allow_html=True)
            # st.markdown(f"""
            # <div class="pr-summary">
            #     <h3>#{pr['PR Number']}{pr['Title']}</h3>
            #     <p>
            #         <span class="small-text">
            #             <strong>PR:</strong> <a href="{pr['URL']}" target="_blank">#{pr['PR Number']}</a> | 
            #             <strong>Repository:</strong> {pr['Repository']} | 
            #             <strong>Author:</strong> {pr['Author']} | 
            #             <strong>Merged:</strong> {pr['Merged At'].strftime('%Y-%m-%d %H:%M')} |
            #             <strong>Changes:</strong> +{pr['Additions']} -{pr['Deletions']} lines
            #         </span>
            #     </p>
            #     <div class="card">
            #         {pr['Summary']}
            #     </div>
            # </div>
            # """, unsafe_allow_html=True)

# ------------------- TAB 2: Open PRs -------------------
with tab2:
    st.markdown("<h2 class='subheader'>Open Pull Requests Review</h2>", unsafe_allow_html=True)
    st.markdown("""
    Get AI-powered code quality reviews for currently open pull requests.
    This helps identify potential issues before merging.
    """)
    
    if st.button("Review Open PRs", type="primary", use_container_width=True):
        all_open_prs = []
        
        for repo in selected_repo_list:
            with st.spinner(f"Fetching open PRs for {repo}..."):
                open_prs = fetch_prs(repo, token, since.isoformat(), until.isoformat(), state="open")
                
                if open_prs:
                    st.success(f"Found {len(open_prs)} open PR(s) in {repo}")
                    
                    progress_bar = st.progress(0)
                    pr_data = []
                    
                    for i, pr in enumerate(open_prs):
                        with st.spinner(f"Reviewing PR #{pr['number']}..."):
                            diff = get_diff(repo, pr['number'], token)
                            review_feedback = review_pr(diff)
                            
                            created_date = datetime.strptime(pr['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                            
                            pr_info = {
                                "Repository": repo,
                                "PR Number": pr['number'],
                                "Title": pr['title'],
                                "Author": pr['user']['login'],
                                "Created At": created_date,
                                "URL": pr['html_url'],
                                "Review": review_feedback,
                                "Additions": pr.get('additions', 0),
                                "Deletions": pr.get('deletions', 0)
                            }
                            pr_data.append(pr_info)
                        
                        # Update progress bar
                        progress_bar.progress((i + 1) / len(open_prs))
                    
                    all_open_prs.extend(pr_data)
                else:
                    st.info(f"No open PRs found for {repo} in the selected date range")
        
        st.session_state.open_prs = all_open_prs
    
    # Display open PRs if available
    if st.session_state.open_prs:
        # st.markdown(f"## Found {len(st.session_state.open_prs)} Open PRs")
        st.markdown(f"""
            <div style="
                display:inline-block;
                background:#e1ecf4;
                color:#0366d6;
                font-weight:600;
                padding:4px 12px;
                border-radius:20px;
                font-size:16px;
            ">
            🟢&nbsp;Found {len(st.session_state.open_prs)} Open PR(s)
            </div>
            """, unsafe_allow_html=True)
        
        # Sort by created date, newest first
        sorted_prs = sorted(st.session_state.open_prs, key=lambda x: x['Created At'], reverse=True)
        
        # Group by repository
        repos = list(set(pr['Repository'] for pr in sorted_prs))
        
        # Repository filter
        if len(repos) > 1:
            selected_repo = st.selectbox("Filter by Repository", ["All"] + repos, key="open_pr_repo_filter")
        else:
            selected_repo = "All"
        
        # Filter PRs by repository if needed
        if selected_repo != "All":
            display_prs = [pr for pr in sorted_prs if pr['Repository'] == selected_repo]
        else:
            display_prs = sorted_prs
        
        # Display PRs as cards
        for pr in display_prs:
            with st.container():
                # Calculate PR age in days
                pr_age = (datetime.now() - pr['Created At']).days
                age_color = "#28a745" if pr_age < 3 else "#dbab09" if pr_age < 7 else "#d73a49"
                
                st.markdown(f"""
                <div class="pr-summary">
                     <h3 style="margin:0;">
                        <a href="{pr['URL']}" target="_blank" style="text-decoration:none; color:#1a237e;">
                        #{pr['PR Number']} - {pr['Title']}
                        </a>
                    </h3>
                    <p>
                        <span class="small-text">
                            <strong>Repository:</strong> {pr['Repository']} | 
                            <strong>Author:</strong> {pr['Author']} | 
                            <strong>Created:</strong> {pr['Created At'].strftime('%Y-%m-%d %H:%M')} |
                            <strong>Age:</strong> <span style="color: {age_color};">{pr_age} days</span>
                        </span>
                    </p>
                    <div class="card">
                        {pr['Review']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ------------------- TAB 3: PR Metrics -------------------
with tab3:
    st.markdown("<h2 class='subheader'>PR Metrics & Analytics</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        Analyze PR metrics to gain insights into your team's workflow and performance.
        Metrics help identify bottlenecks and areas for improvement.
        """)
    with col2:
        pr_state_option = st.selectbox(
            "Select PR Type",
            options=["All", "Open", "Merged"],
            index=0,
            help="Filter metrics by PR state"
        )
    
    # Map UI option to GitHub API state
    pr_state = "all" if pr_state_option == "All" else "open" if pr_state_option == "Open" else "closed"
    
    if st.button("Generate PR Metrics", type="primary", use_container_width=True):
        all_metrics = []
        all_prs = []
        
        with st.spinner(f"Fetching and analyzing {pr_state_option.lower()} PRs..."):
            for repo in selected_repo_list:
                try:
                    prs = fetch_prs(repo, token, since.isoformat(), until.isoformat(), state=pr_state)
                    if prs:
                        prs = add_pr_analytics(repo, prs)
                        all_prs.extend(prs)
                        df = analyze_pr_metrics(repo, prs)
                        df["Repository"] = repo
                        df["PR Link"] = df["PR Number"].apply(
                            lambda pr: f"<a href='https://github.com/{repo}/pull/{pr}' target='_blank'>#{pr}</a>"
                        )
                        all_metrics.append(df)
                except Exception as e:
                    st.error(f"Error analyzing {repo}: {e}")
        
        if all_prs:
            # Add analytics data
            st.session_state.all_prs = all_prs
            
            if all_metrics:
                full_df = pd.concat(all_metrics, ignore_index=True)
                st.session_state.metrics_df = full_df
        else:
            st.warning(f"No {pr_state_option.lower()} PRs found for the selected repositories in this date range.")
    
    # Display metrics if available
    if hasattr(st.session_state, 'all_prs') and st.session_state.all_prs:
        all_prs = st.session_state.all_prs
        
        # Calculate metrics
        merged_prs = [pr for pr in all_prs if pr.get("merged_at")]
        open_prs = [pr for pr in all_prs if pr.get("state") == "open"]
        closed_not_merged_prs = [
            pr for pr in all_prs
            if pr.get("state") == "closed" and not pr.get("merged_at")
        ]
        
        # Calculate review durations for merged PRs
        review_durations = [
            (pd.to_datetime(pr["merged_at"]) - pd.to_datetime(pr["created_at"])).total_seconds() / 3600
            for pr in all_prs if pr.get("merged_at") and pr.get("created_at")
        ]
        avg_duration = sum(review_durations) / len(review_durations) if review_durations else 0
        
        # Calculate average PR size
        avg_size = sum(
            pr.get("additions", 0) + pr.get("deletions", 0) for pr in all_prs
        ) / len(all_prs) if all_prs else 0
        
        # Calculate average comments per PR
        comments_per_pr = [
            pr.get("comments", 0) + pr.get("review_comments", 0) for pr in all_prs
        ]
        avg_comments = sum(comments_per_pr) / len(comments_per_pr) if comments_per_pr else 0
        
        # Calculate PRs merged without comments
        pr_no_comments = [
            pr for pr in all_prs if pr.get("merged_at") and pr.get("review_comments", 0) == 0
        ]
        
        # Display metrics in a nice dashboard style
        st.markdown("<h3 class='subheader'>📈 PR Summary</h3>", unsafe_allow_html=True)
        
        # First row of metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(all_prs)}</div>
                <div class="metric-label">Total PRs</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(open_prs)}</div>
                <div class="metric-label">Open PRs</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(merged_prs)}</div>
                <div class="metric-label">Merged PRs</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(closed_not_merged_prs)}</div>
                <div class="metric-label">Closed (Not Merged)</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Second row of detailed metrics
        st.markdown("<h3 class='subheader'>📊 PR Analytics</h3>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_duration:.1f}</div>
                <div class="metric-label">Avg Review Time (hrs)</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_size:.0f}</div>
                <div class="metric-label">Avg PR Size (LoC)</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{avg_comments:.1f}</div>
                <div class="metric-label">Avg Comments per PR</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{len(pr_no_comments)}</div>
                <div class="metric-label">Merged w/o Comments</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Data visualizations
        st.markdown("<h3 class='subheader'>📊 Visualizations</h3>", unsafe_allow_html=True)
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["PR Timeline", "PR Size Distribution", "Author Activity"])
        
        with viz_tab1:
            # Create timeline data
            if merged_prs:
                timeline_data = []
                for pr in merged_prs:
                    created_at = pd.to_datetime(pr["created_at"])
                    merged_at = pd.to_datetime(pr["merged_at"])
                    repo = pr.get("base", {}).get("repo", {}).get("name", "Unknown")
                    
                    timeline_data.append({
                        "PR": f"#{pr['number']} {pr['title'][:30]}...",
                        "Repository": repo,
                        "Start": created_at,
                        "End": merged_at,
                        "Duration (hrs)": (merged_at - created_at).total_seconds() / 3600
                    })
                
                if timeline_data:
                    timeline_df = pd.DataFrame(timeline_data)
                    timeline_df = timeline_df.sort_values("Start")
                    
                    # Create a Gantt chart
                    fig = px.timeline(
                        timeline_df, 
                        x_start="Start", 
                        x_end="End", 
                        y="PR",
                        color="Repository",
                        hover_data=["Duration (hrs)"]
                    )
                    fig.update_layout(
                        title="PR Timeline (Creation to Merge)",
                        height=max(500, len(timeline_df) * 30),
                        xaxis_title="Date",
                        yaxis_title="Pull Request"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No merged PRs available for timeline visualization")
            else:
                st.info("No merged PRs available for timeline visualization")
        
        with viz_tab2:
            # PR size distribution
            if all_prs:
                size_data = []
                for pr in all_prs:
                    size_data.append({
                        "PR": f"#{pr['number']}",
                        "Title": pr['title'],
                        "Size": pr.get("additions", 0) + pr.get("deletions", 0),
                        "Additions": pr.get("additions", 0),
                        "Deletions": pr.get("deletions", 0),
                        "Repository": pr.get("base", {}).get("repo", {}).get("name", "Unknown"),
                        "State": pr.get("state", "unknown").capitalize()
                    })
                
                if size_data:
                    size_df = pd.DataFrame(size_data)
                    
                    # Create stacked bar chart for additions/deletions
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=size_df["PR"],
                        y=size_df["Additions"],
                        name="Additions",
                        marker_color="#28a745"
                    ))
                    fig.add_trace(go.Bar(
                        x=size_df["PR"],
                        y=size_df["Deletions"],
                        name="Deletions",
                        marker_color="#d73a49"
                    ))
                    
                    fig.update_layout(
                        title="PR Size Distribution (Additions & Deletions)",
                        barmode="stack",
                        height=500,
                        xaxis_title="Pull Request",
                        yaxis_title="Lines of Code",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No PR size data available for visualization")
            else:
                st.info("No PRs available for size distribution visualization")
        
        with viz_tab3:
            # Author activity
            if all_prs:
                author_data = {}
                for pr in all_prs:
                    author = pr["user"]["login"]
                    if author not in author_data:
                        author_data[author] = {"count": 0, "additions": 0, "deletions": 0}
                    
                    author_data[author]["count"] += 1
                    author_data[author]["additions"] += pr.get("additions", 0)
                    author_data[author]["deletions"] += pr.get("deletions", 0)
                
                if author_data:
                    author_df = pd.DataFrame([
                        {
                            "Author": author,
                            "PR Count": data["count"],
                            "Additions": data["additions"],
                            "Deletions": data["deletions"],
                            "Total Changes": data["additions"] + data["deletions"]
                        }
                        for author, data in author_data.items()
                    ])
                    
                    # Sort by PR count
                    author_df = author_df.sort_values("PR Count", ascending=False)
                    
                    # Create bar chart
                    fig = px.bar(
                        author_df,
                        x="Author",
                        y="PR Count",
                        color="Total Changes",
                        text="PR Count",
                        hover_data=["Additions", "Deletions", "Total Changes"]
                    )
                    
                    fig.update_layout(
                        title="Author Activity",
                        height=500,
                        xaxis_title="Author",
                        yaxis_title="Number of PRs",
                        coloraxis_colorbar_title="Total Changes"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No author activity data available for visualization")
            else:
                st.info("No PRs available for author activity visualization")
        
        # Detailed metrics table
        if st.session_state.metrics_df is not None:
            st.markdown("<h3 class='subheader'>🔢 Detailed PR Metrics</h3>", unsafe_allow_html=True)
            
            # Reorder columns for better readability
            columns = ["PR Link", "Repository", "Author", "Lines Changed", "Comments",
                       "Reviewers", "First Review (hrs)", "Merged Without Comments"]
            
            metrics_df = st.session_state.metrics_df[columns]
            
            # Add search and filter options
            search_col1, search_col2 = st.columns([3, 1])
            with search_col1:
                search_term = st.text_input("Search PRs", placeholder="Enter author name, PR number, etc.")
            with search_col2:
                sort_by = st.selectbox("Sort by", options=[
                    "Lines Changed", "Comments", "First Review (hrs)", "Reviewers"
                ])
            
            # Apply filters
            filtered_df = metrics_df
            if search_term:
                filtered_df = metrics_df[
                    metrics_df.astype(str).apply(
                        lambda row: row.str.contains(search_term, case=False).any(), axis=1
                    )
                ]
            
            # Sort data
            filtered_df = filtered_df.sort_values(by=sort_by, ascending=False)
            
            # Display the table with working hyperlinks
            st.markdown(f"Found {len(filtered_df)} PRs matching your criteria")
            st.write(filtered_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Provide download option
            csv_df = filtered_df.copy()
            csv_df["PR Link"] = csv_df["PR Link"].str.extract(r"href='(.*?)'")
            
            st.download_button(
                "📥 Download Metrics CSV",
                csv_df.to_csv(index=False),
                "pr_metrics.csv",
                "text/csv",
                use_container_width=True
            )

# ------------------- TAB 4: Security Scans -------------------
with tab4:
    st.markdown("<h2 class='subheader'>Security Scan Results</h2>", unsafe_allow_html=True)
    st.markdown("""
    Monitor code security alerts from CodeQL scans for your repositories.
    Identify and prioritize security vulnerabilities to address.
    """)
    
    if st.button("Fetch Security Alerts", type="primary", use_container_width=True):
        all_alerts = {}
        
        with st.spinner("Fetching CodeQL alerts..."):
            for repo in selected_repo_list:
                try:
                    alerts = fetch_codeql_alerts(repo, token)
                    all_alerts[repo] = alerts
                    if alerts:
                        st.warning(f"Found {len(alerts)} security alerts in {repo}")
                    else:
                        st.success(f"✅ No security alerts found in {repo}")
                except Exception as e:
                    st.error(f"Error fetching alerts for {repo}: {e}")
        
        st.session_state.alerts = all_alerts
    
    # Display security alerts if available
    if st.session_state.alerts:
        total_alerts = sum(len(alerts) for alerts in st.session_state.alerts.values())
        
        if total_alerts == 0:
            st.success("✅ No security alerts found across all repositories!")
        else:
            st.warning(f"⚠️ Found {total_alerts} security alerts across all repositories")
            
            # Create severity distribution chart
            severity_counts = {"Critical": 0, "Error": 0,"High": 0, "Medium": 0, "Low": 0, "Unknown": 0}
            
            for repo, alerts in st.session_state.alerts.items():
                for alert in alerts:
                    severity = alert.get("rule", {}).get("severity", "unknown").capitalize()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                    else:
                        severity_counts["Unknown"] += 1
            
            # Create pie chart for severity distribution
            if sum(severity_counts.values()) > 0:
                fig = px.pie(
                    values=list(severity_counts.values()),
                    names=list(severity_counts.keys()),
                    title="Alert Severity Distribution",
                    color=list(severity_counts.keys()),
                    color_discrete_map={
                        "Critical": "#d73a49",
                        "Error": "#d73a49",
                        "High": "#e36209",
                        "Medium": "#dbab09",
                        "Low": "#28a745",
                        "Unknown": "#6a737d"
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            # Display alerts grouped by repository
            st.markdown("<h3 class='subheader'>Alert Details</h3>", unsafe_allow_html=True)
            
            # Create tabs for repositories with alerts
            repos_with_alerts = [repo for repo, alerts in st.session_state.alerts.items() if alerts]
            
            if repos_with_alerts:
                tabs = st.tabs(repos_with_alerts)
                
                for i, repo in enumerate(repos_with_alerts):
                    with tabs[i]:
                        alerts = st.session_state.alerts[repo]
                        
                        # Group alerts by severity
                        severity_groups = {}
                        for alert in alerts:
                            severity = alert.get("rule", {}).get("severity", "unknown").capitalize()
                            if severity not in severity_groups:
                                severity_groups[severity] = []
                            severity_groups[severity].append(alert)
                        
                        # Display alerts by severity (highest first)
                        severity_order = ["Critical","Error", "High", "Medium", "Low", "Unknown"]
                        
                        for severity in severity_order:
                            if severity in severity_groups:
                                st.markdown(f"#### {severity} Severity ({len(severity_groups[severity])})")
                                
                                for alert in severity_groups[severity]:
                                    # Extract alert details
                                    rule = alert.get("rule", {})
                                    description = rule.get("description", "No description")
                                    tool_name = alert.get("tool", {}).get("name", "CodeQL")
                                    location = alert.get("most_recent_instance", {}).get("location", {})
                                    file_path = location.get("path", "Unknown")
                                    start_line = location.get("start_line", 0)
                                    timestamp = alert.get("created_at", "")
                                    ref = alert.get("ref", "refs/heads/main").split("/")[-1]
                                    url = alert.get("html_url", f"https://github.com/{repo}/security/code-scanning")
                                    
                                    # Calculate relative time
                                    if timestamp:
                                        created_at = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                                        now = datetime.now(timezone.utc)
                                        hours_ago = int((now - created_at).total_seconds() // 3600)
                                        time_display = f"{hours_ago} hours ago"
                                    else:
                                        time_display = "some time ago"
                                    
                                    # Severity color map
                                    severity_colors = {
                                        "Critical": "#d73a49",
                                        "Error": "#d73a49",
                                        "High": "#e36209",
                                        "Medium": "#dbab09",
                                        "Low": "#28a745",
                                        "Unknown": "#6a737d"
                                    }
                                    severity_color = severity_colors.get(severity, "#6a737d")
                                    
                                    # Create alert card
                                    st.markdown(f"""
                                    <div class="card alert-{severity.lower()}">
                                        <div style="display: flex; align-items: center; justify-content: space-between;">
                                            <div>
                                                <a href="{url}" target="_blank" style="text-decoration: none;">
                                                    <strong style="font-size: 16px;">{description}</strong>
                                                </a>
                                                <span style="background-color: {severity_color}1A; color: {severity_color}; 
                                                    border: 1px solid {severity_color}; border-radius: 16px; 
                                                    padding: 2px 8px; font-size: 12px; margin-left: 10px;">
                                                    {severity}
                                                </span>
                                            </div>
                                            <div>
                                                <a href="{url}" target="_blank" class="btn" 
                                                   style="background-color: #0366d6; color: white; 
                                                   padding: 5px 10px; border-radius: 4px; 
                                                   text-decoration: none; font-size: 12px;">
                                                    View Alert
                                                </a>
                                            </div>
                                        </div>
                                        <div style="color: #586069; font-size: 13px; margin-top: 6px;">
                                            <strong>Location:</strong> <code>{file_path}:{start_line}</code><br>
                                            <strong>Detected by:</strong> {tool_name} • <strong>Created:</strong> {time_display}
                                        </div>
                                        <div style="margin-top: 6px;">
                                            <span style="background-color: #e1ecf4; color: #0366d6; 
                                                padding: 2px 8px; font-size: 12px; border-radius: 20px;">
                                                Branch: {ref}
                                            </span>
                                            <span style="background-color: #e1ecf4; color: #0366d6; 
                                                padding: 2px 8px; font-size: 12px; border-radius: 20px; margin-left: 5px;">
                                                Alert #{alert.get("number", "1")}
                                            </span>
                                        </div>
                                    </div>
                                    <div style="margin-bottom: 15px;"></div>
                                    """, unsafe_allow_html=True)

# ------------------- TAB 5: Admin Metrics (Static Mocked Data, 3-Column Layout) -------------------
with tab5:
    render_admin_tab()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 30px; padding: 20px; color: #666;">
    <p>PR Review Assistant - AI-powered code review and PR analytics</p>
    <p style="font-size: 0.8rem;">Developed by NexusInnovate • Powered by AI</p>
</div>
""", unsafe_allow_html=True)