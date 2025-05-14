import requests
from datetime import datetime

GITHUB_API = "https://api.github.com"

def fetch_prs(repo, token, since, until):
    url = f"{GITHUB_API}/repos/{repo}/pulls"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100}
    
    response = requests.get(url, headers=headers, params=params, verify=False)
    all_prs = response.json()
    print("prs: ", all_prs)
    
    merged_prs = [
        pr for pr in all_prs
        if pr["merged_at"] and since <= pr["merged_at"] <= until
    ]
    return merged_prs

def get_diff(repo, pr_number, token):
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(url, headers=headers, verify=False)
    return response.text
