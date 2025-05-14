import streamlit as st
from github_utils import fetch_prs, get_diff
from ai_summarizer import summarize_diff
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

st.title("🔍 AI PR Summary Dashboard")

repo = st.text_input("GitHub Repository (e.g. openai/gpt-4)", "your-org/your-repo")
# repo = "vamshikarru01/ai-pr-summarizer"
# token = st.text_input("GitHub Token", type="password")
token = os.getenv("GITHUB_TOKEN")

since = st.date_input("Start Date")
until = st.date_input("End Date")

if st.button("Generate Summaries"):
    st.info("Fetching PRs...")
    prs = fetch_prs(repo, token, since.isoformat(), until.isoformat())

    st.success(f"Found {len(prs)} merged PRs.")
    
    for pr in prs:
        st.subheader(f"#{pr['number']} - {pr['title']}")
        st.caption(f"Author: {pr['user']['login']} • Merged: {pr['merged_at']}")
        with st.spinner("Summarizing..."):
            diff = get_diff(repo, pr['number'], token)
            summary = summarize_diff(diff)
            st.code(summary, language="markdown")
