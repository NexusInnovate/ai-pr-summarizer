import requests
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
GITHUB_API = os.getenv("GITHUB_API")

def fetch_prs(repo, token, since, until, state):
    url = f"{GITHUB_API}/repos/{repo}/pulls"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"state": {state}, "sort": "updated", "direction": "desc", "per_page": 100}
    
    response = requests.get(url, headers=headers, params=params, verify=False)
    all_prs = response.json()
    # print("prs: ", all_prs)
    if state == "closed":
        all_prs = [
            pr for pr in all_prs
            if pr["merged_at"] and since <= pr["merged_at"] <= until
            ]
        
    return all_prs

def get_diff(repo, pr_number, token):
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(url, headers=headers, verify=False)
    return response.text

def find_all_repo_names(data):
    result = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "full_name":
                result.append(value)
            elif isinstance(value, (dict, list)):
                result.extend(find_all_repo_names(value))
    elif isinstance(data, list):
        for item in data:
            result.extend(find_all_repo_names(item))
    return result

def fetch_org_repos(org, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"{GITHUB_API}/orgs/{org}/repos"
    response = requests.get(url, headers=headers, verify=False)
    data = response.json()
    repos = find_all_repo_names(data)
    return repos

def fetch_codeql_alerts(repo, token, state="open"):
    """
    Fetches CodeQL alerts for a given GitHub repository.
    """
    url = f"{GITHUB_API}/repos/{repo}/code-scanning/alerts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    params = {
        "state": state,
        "per_page": 100
    }

    response = requests.get(url, headers=headers, params=params, verify=False)
    
    if response.status_code == 200:
        print("codeql: ", response.json())
        return response.json()
    else:
        print(f"⚠️ Failed to fetch CodeQL alerts: {response.status_code} - {response.text}")
        return []