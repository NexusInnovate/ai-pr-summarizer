import os
import requests
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import httpx

load_dotenv()

GITHUB_API = os.getenv("GITHUB_API")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY, http_client=httpx.Client(verify=False))


def fetch_prs(repo, token, since, until, state="closed"):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.github.com/repos/{repo}/pulls?state={state}&per_page=100&sort=created&direction=desc"
    response = requests.get(url, headers=headers)
    all_prs = response.json()

    filtered = [
        pr for pr in all_prs
        if since <= pr['created_at'][:10] <= until
    ]
    return filtered

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
            "PR Number": pr_number,
            "Author": pr['user']['login'],
            "Lines Changed": lines_changed,
            "Comments": comment_count,
            "Reviewers": ", ".join(reviewers),
            "First Review (hrs)": round(time_to_first_review, 2) if time_to_first_review else "N/A",
            "Merged Without Comments": "Yes" if comment_count == 0 else "No"
        })

    return pd.DataFrame(metrics)
