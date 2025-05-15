import streamlit as st
from github_utils import fetch_prs, get_diff
from ai_summarizer import summarize_diff, review_pr
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv
load_dotenv()

st.title("🤖 PR Review Assistant (AI Powered)")

repo = st.text_input("GitHub Repository", "your-org/your-repo")
# repo = "vamshikarru01/ai-pr-summarizer"
# token = st.text_input("GitHub Token", type="password")
token = os.getenv("GITHUB_TOKEN")

since = st.date_input("Start Date")
until = st.date_input("End Date")

tab1, tab2 = st.tabs(["Merged PRs Summary", "Open PRs Review"])

# ------------------- TAB 1: Merged PRs -------------------
with tab1:
    if st.button("Generate Summaries"):
        if not repo or not token:
            st.error("Missing GitHub repo or token.")
        else:
            st.info("Fetching PRs...")
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
                st.markdown("## PR Summary Table")
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
        if not repo or not token:
            st.error("Missing GitHub repo or token.")
        else:
            st.info("Fetching Open PRs...")
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
                st.markdown("## PR Summary Table")
                df = pd.DataFrame(st.session_state.open_prs)
                for i, row in df.iterrows():
                    st.markdown("---")
                    cols = st.columns([1.5, 2, 3])  # Adjust column widths
                    cols[0].markdown(f"**{row['Title']}**")
                    cols[1].markdown(row['Metadata'], unsafe_allow_html=True)
                    cols[2].markdown(row['Summary'], unsafe_allow_html=True)
