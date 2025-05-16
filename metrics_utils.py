import os
import requests
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

GITHUB_API = os.getenv("GITHUB_API")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_pr_comments(repo, pr_number):
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers, verify=False)
    return response.json()

def get_pr_timeline(repo, pr_number):
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/timeline"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.mockingbird-preview"
    }
    response = requests.get(url, headers=headers, verify=False)
    return response.json()

def get_pr_diff_stats(repo, pr_number):
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers, verify=False)
    return response.json()

def analyze_pr_metrics(repo, prs):
    metrics = []
    for pr in prs:
        pr_number = pr['number']
        pr_url = pr['html_url']  # <- Add this line

        created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
        merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00')) if pr['merged_at'] else None

        comments = get_pr_comments(repo, pr_number)
        timeline = get_pr_timeline(repo, pr_number)
        pr_details = get_pr_diff_stats(repo, pr_number)

        reviewers = list(set([c['user']['login'] for c in comments]))
        comment_count = len(comments)
        lines_changed = pr_details.get('additions', 0) + pr_details.get('deletions', 0)

        first_review_time = None
        for event in timeline:
            if event['event'] == 'reviewed':
                first_review_time = datetime.fromisoformat(event['submitted_at'].replace('Z', '+00:00'))
                break

        time_to_first_review = (first_review_time - created).total_seconds() / 3600 if first_review_time else None

        metrics.append({
            "Repository": repo,
            "PR Number": f"[#{pr_number}]({pr_url})",  # <- Hyperlink format for Streamlit Markdown tables
            "Author": pr['user']['login'],
            "Lines Changed": lines_changed,
            "Comments": comment_count,
            "Reviewers": ", ".join(reviewers),
            "First Review (hrs)": round(time_to_first_review, 2) if time_to_first_review else "N/A",
            "Merged Without Comments": "Yes" if comment_count == 0 else "No"
        })

    return pd.DataFrame(metrics)


def add_pr_analytics(repo, all_prs):
    # Fetch additions/deletions via per-PR API
    print("repo variables....", repo)
    # print("all_prs", all_prs)
    for pr in all_prs:
        pr_number = pr["number"]
        print("1-additions...", pr_number)
        pr_details = get_pr_diff_stats(repo, pr_number)
        pr["additions"] = pr_details.get('additions', 0)
        print("1-additions...", pr["additions"])
        pr["deletions"] = pr_details.get('deletions', 0)
        pr["comments"] = pr_details.get("comments", 0)
        pr["review_comments"] = pr_details.get("review_comments", 0)

    return all_prs