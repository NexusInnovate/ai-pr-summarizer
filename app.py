import streamlit as st
from github_utils import fetch_prs, get_diff, fetch_org_repos
from db_utils import fetch_pr_details_by_id, insert_pr_details
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

tab1, tab2, tab3 = st.tabs(["Merged PRs Summary", "Open PRs Review", "PR Metrics"])

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
                  pr_id = repo + str(pr['number']) 
                  print(f"prid: {pr_id}") 
                  summary = fetch_pr_details_by_id("Merged_PR_Reviews.db", "GENERATE_SUMMARIES", pr_id) 
                  if not summary:
                    diff = get_diff(repo, pr['number'], token)
                    insert_pr_details("Merged_PR_Reviews.db", "GENERATE_SUMMARIES", pr_id, diff)
                    print(f"inserted summary for PR id: {pr_id}")
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
                    pr_id = repo + str(pr['number']) 
                    print(f"prid: {pr_id}") 
                    diff = fetch_pr_details_by_id("Open_PR_Reviews.db", "CHECK_OPEN_PR_REVIEW", pr_id) 
                    if not diff:
                        diff = get_diff(repo, pr['number'], token)
                        insert_pr_details("Open_PR_Reviews.db", "CHECK_OPEN_PR_REVIEW", pr_id, diff)
                        print(f"inserted quality_feedback PR id: {pr_id}")
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

