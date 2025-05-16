# admin_dashboard.py

import streamlit as st
import pandas as pd

def render_admin_tab():
    st.title("📊 Admin Metrics Dashboard")

    # Sprint Summary (full-width)
    with st.container():
        st.markdown("### Sprint Summary")
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
        st.markdown("### Features Released in Sprint 21")
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
            st.markdown("### Total PRs")
            st.markdown("""
            <div style="border:2px solid #dedede; border-radius: 8px; padding: 10px; background-color: #fff;">
            <h2 style="text-align:center;">34</h2>
            <p style="text-align:center;">Merged pull requests</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown("### Open PRs")
            st.markdown("""
            <div style="border:2px solid #dedede; border-radius: 8px; padding: 10px; background-color: #fff8e1;">
            <h2 style="text-align:center;">5</h2>
            <p style="text-align:center;">Still in review</p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        with st.container():
            st.markdown("### Code Reviews Done")
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
            st.markdown("### Review Comments")
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
