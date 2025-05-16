import streamlit as st
from github_utils import fetch_prs, get_diff, fetch_org_repos
from ai_summarizer import summarize_diff, review_pr
from metrics_utils import analyze_pr_metrics
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

st.title("🤖 PR Review Assistant (AI Powered)")

org = st.text_input("GitHub Org", "NexusInnovate")
# repo = "vamshikarru01/ai-pr-summarizer"
# token = st.text_input("GitHub Token", type="password")
token = os.getenv("GITHUB_TOKEN")

since = st.date_input("Start Date")
until = st.date_input("End Date")

#---------------------To Fetch List of Repos and PRs---------
selected_repo_list = []
if org and token:
    repo_names_list = fetch_org_repos(org, token)
    if repo_names_list:
        selected_repo_list =  st.multiselect(f"select repos from {org} for PR summary and review details ", repo_names_list)
    else:
        st.warning(f"No repositories under {org}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Merged PRs Summary", "Open PRs Review", "PR Metrics", "Tab 4 (Optional)", "📊 Admin Metrics"])

# ------------------- TAB 1: Merged PRs -------------------
with tab1:
    if st.button("Generate Summaries"):
        if not selected_repo_list or not token:
            st.error("Missing GitHub repo or token.")
        else:
          for repo in selected_repo_list:  
            st.info(f"Fetching PRs for {repo}...")
            prs = fetch_prs(repo, token, since.isoformat(), until.isoformat(), state="closed")
            st.success(f"✅ Found {len(prs)} merged PR(s).")

            pr_data = []  # List to collect rows for the table

            for pr in prs:
                with st.spinner("🔍 Summarizing..."):
                    diff = get_diff(repo, pr['number'], token)
                    summary = summarize_diff(diff)

                # Collect table data
                title = f"#{pr['number']} - {pr['title']}"
                metadata = (
                    f"<strong>Author:</strong> {pr['user']['login']}<br>"
                    f"<strong>Merged at:</strong> {pr['merged_at']}<br>"
                    f"<a href='{pr['html_url']}' target='_blank'>View PR</a>"
                )

                pr_data.append({
                    "Title": title,
                    "Metadata": metadata,
                    "Summary": summary
                })

            # Display the table after all PRs are processed
            if pr_data:
                st.markdown(f"## PR Summary Table for {repo}")
                df = pd.DataFrame(pr_data)
                # st.table(df)
                # st.dataframe(df)  # or use st.table(df) for a static table
                # Render as Markdown table with wrapped columns
                for i, row in df.iterrows():
                    st.markdown("---")
                    cols = st.columns([1.5, 2, 3])  # Adjust column widths
                    cols[0].markdown(f"**{row['Title']}**")
                    cols[1].markdown(row['Metadata'], unsafe_allow_html=True)
                    cols[2].markdown(row['Summary'], unsafe_allow_html=True)

# ------------------- TAB 2: Open PRs -------------------
with tab2:
    if st.button("Check Open PRs Review"):
        if not selected_repo_list or not token:
            st.error("Missing GitHub repo or token.")
        else:
          for repo in selected_repo_list:  
            st.info(f"Fetching Open PRs for {repo}...")
            open_prs = fetch_prs(repo, token, since.isoformat(), until.isoformat(), state="open")
            st.success(f"🔍 Found {len(open_prs)} open PR(s).")
            pr_data = []

            for pr in open_prs:
                with st.spinner(f"Analyzing PR #{pr['number']}..."):
                    diff = get_diff(repo, pr['number'], token)
                    quality_feedback = review_pr(diff)

                title = f"#{pr['number']} - {pr['title']}"
                metadata = (
                    f"<strong>Author:</strong> {pr['user']['login']}<br>"
                    f"<a href='{pr['html_url']}' target='_blank'>View PR</a>"
                )

                pr_data.append({
                    "Title": title,
                    "Metadata": metadata,
                    "Summary": quality_feedback
                })
            st.session_state.open_prs = pr_data

            # Display the table after all PRs are processed
            if st.session_state.open_prs:
                st.markdown(f"## PR Summary Table for {repo}")
                df = pd.DataFrame(st.session_state.open_prs)
                for i, row in df.iterrows():
                    st.markdown("---")
                    cols = st.columns([1.5, 2, 3])  # Adjust column widths
                    cols[0].markdown(f"**{row['Title']}**")
                    cols[1].markdown(row['Metadata'], unsafe_allow_html=True)
                    cols[2].markdown(row['Summary'], unsafe_allow_html=True)

# ------------------- TAB 3: PR Metrics  -------------------
with tab3:
    pr_state_option = st.selectbox(
        "Select PR Type for Metrics",
        options=["All", "Open", "Merged"],
        index=0
    )

    # Map UI option to GitHub API state
    pr_state = "all" if pr_state_option == "All" else "open" if pr_state_option == "Open" else "closed"

    if st.button("Generate PR Metrics"):
        if not selected_repo_list or not token:
            st.error("Missing GitHub repo or token.")
        else:
            all_metrics = []
            st.info(f"Fetching {pr_state_option.lower()} PRs for metrics analysis...")

            for repo in selected_repo_list:
                try:
                    st.write(f"📊 Analyzing {repo}...")
                    prs = fetch_prs(repo, token, since.isoformat(), until.isoformat(), state=pr_state)
                    if prs:
                        df = analyze_pr_metrics(repo, prs)
                        df["Repository"] = repo
                        df["PR Link"] = df["PR Number"].apply(
                            lambda pr: f"<a href='https://github.com/{repo}/pull/{pr}' target='_blank'>#{pr}</a>"
                        )
                        all_metrics.append(df)
                    else:
                        st.warning(f"No {pr_state_option.lower()} PRs found for {repo} in this date range.")
                except Exception as e:
                    st.error(f"Error analyzing {repo}: {e}")

            if all_metrics:
                full_df = pd.concat(all_metrics, ignore_index=True)

                # Reorder columns to show PR Link first
                columns = ["PR Link", "Repository", "Author", "Lines Changed", "Comments",
                           "Reviewers", "First Review (hrs)", "Merged Without Comments"]
                full_df = full_df[columns]

                # Render HTML table with working hyperlinks
                st.markdown("## 🔢 PR Metrics Summary")
                st.write(full_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                # Prepare CSV without HTML
                csv_df = full_df.copy()
                csv_df["PR Link"] = csv_df["PR Link"].str.extract(r"href='(.*?)'")
                st.download_button("Download All Metrics CSV", csv_df.to_csv(index=False), "all_pr_metrics.csv", "text/csv")
            else:
                st.warning("No PR metrics to display.")
with tab4:
    st.header("")

# ------------------- TAB 5: Admin Metrics (Static Mocked Data) -------------------

# ------------------- TAB 5: Admin Metrics (Static Mocked Data, 3-Column Layout) -------------------
with tab5:
    st.title("📊 Admin Metrics Dashboard")

    # Sprint Summary (full-width)
    with st.container():
        st.markdown("### 📝 Sprint Summary")
        st.markdown("""
        <div style="border:1px solid #ccc; border-radius: 10px; padding: 15px; background-color: #f9f9f9;">
        <ul>
            <li><strong>Story 1:</strong> Enable AI-powered PR summarization for merged pull requests.</li>
            <li><strong>Story 2:</strong> Integrate quality feedback mechanism for open pull requests.</li>
            <li><strong>Story 3:</strong> Build dashboard with developer and repo metrics.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    # Features Released (full-width)
    with st.container():
        st.markdown("### 🚀 Features Released in Sprint 21")
        st.markdown("""
        <div style="border:1px solid #ccc; border-radius: 10px; padding: 15px; background-color: #f0faff;">
        <ol>
            <li><a href="https://jira.company.com/browse/DMP-123" target="_blank"><strong>DMP-123</strong></a>: Added AI summarization for PRs.</li>
            <li><a href="https://jira.company.com/browse/DMP-125" target="_blank"><strong>DMP-125</strong></a>: Metrics dashboard for PR analysis.</li>
            <li><a href="https://jira.company.com/browse/DMP-130" target="_blank"><strong>DMP-130</strong></a>: Review quality scoring system.</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

    # Row 1: Total PRs, Open PRs, Code Reviews
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container():
            st.markdown("### 📥 Total PRs")
            st.markdown("""
            <div style="border:2px solid #dedede; border-radius: 8px; padding: 10px; background-color: #fff;">
            <h2 style="text-align:center;">34</h2>
            <p style="text-align:center;">Merged pull requests</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown("### 📤 Open PRs")
            st.markdown("""
            <div style="border:2px solid #dedede; border-radius: 8px; padding: 10px; background-color: #fff8e1;">
            <h2 style="text-align:center;">5</h2>
            <p style="text-align:center;">Still in review</p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        with st.container():
            st.markdown("### 👀 Code Reviews Done")
            st.markdown("""
            <div style="border:2px solid #dedede; border-radius: 8px; padding: 10px; background-color: #f2fff2;">
            <h2 style="text-align:center;">27</h2>
            <p style="text-align:center;">Reviews completed</p>
            </div>
            """, unsafe_allow_html=True)

    # Row 2: Review Comments, Repo with Most PRs, Top Reviewers
    col4, col5, col6 = st.columns(3)
    with col4:
        with st.container():
            st.markdown("### 💬 Review Comments")
            st.markdown("""
            <div style="border:2px solid #dedede; border-radius: 8px; padding: 10px; background-color: #eef6ff;">
            <h2 style="text-align:center;">91</h2>
            <p style="text-align:center;">Comments across PRs</p>
            </div>
            """, unsafe_allow_html=True)

    with col5:
        with st.container():
            st.markdown("### 🏆 Repo with Most PRs")
            st.markdown("""
            <div style="border:1px solid #ccc; border-radius: 10px; padding: 10px; background-color: #fff;">
            <strong>ai-pr-summarizer</strong><br/>
            <span style="font-size: 20px;">12 PRs</span>
            </div>
            """, unsafe_allow_html=True)

    with col6:
        with st.container():
            st.markdown("### 👩‍💻 Top Reviewers")
            top_reviewers = pd.DataFrame({
                "Reviewer": ["alice", "bob", "carol"],
                "Reviews": [10, 8, 7]
            })
            st.dataframe(top_reviewers, use_container_width=True)

    # Row 3: Most Commented PRs, Merged w/o Review, Placeholder for more
    col7, col8, col9 = st.columns(3)
    with col7:
        with st.container():
            st.markdown("### 🧵 Most Commented PRs")
            st.markdown("""
            <div style="border:1px solid #ccc; border-radius: 10px; padding: 10px; background-color: #fff;">
            <ul>
                <li><a href="https://github.com/org/repo/pull/101" target="_blank">#101</a>: 19 comments</li>
                <li><a href="https://github.com/org/repo/pull/95" target="_blank">#95</a>: 15 comments</li>
                <li><a href="https://github.com/org/repo/pull/88" target="_blank">#88</a>: 12 comments</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

    with col8:
        with st.container():
            st.markdown("### ⚠️ Merged Without Review")
            st.markdown("""
            <div style="border:1px solid #ccc; border-radius: 10px; padding: 10px; background-color: #ffecec;">
            <ul>
                <li><a href="https://github.com/org/repo/pull/109" target="_blank">#109</a></li>
                <li><a href="https://github.com/org/repo/pull/91" target="_blank">#91</a></li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

    with col9:
        with st.container():
            st.markdown("### 📈 Upcoming Ideas")
            st.markdown("""
            <div style="border:1px solid #e0e0e0; border-radius: 10px; padding: 10px; background-color: #f5f5f5;">
            <ul>
                <li>Reviewer scoring system</li>
                <li>Automated release notes</li>
                <li>Sprint velocity chart</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
