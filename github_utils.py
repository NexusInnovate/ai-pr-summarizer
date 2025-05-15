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
