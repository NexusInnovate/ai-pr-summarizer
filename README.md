# 🤖 ai-pr-summarizer

AI-Powered PR Summary Bot for Git.

It is a tool that automatically summarizes what changed, why, and how, to help with quicker code reviews and project tracking.

---

## 📄 Environment Setup

Create a `.env` file in the project root and add the following variables:

```env
OPENAI_API_KEY="<API KEY>"
GITHUB_TOKEN="<github token>"
GITHUB_API="https://api.github.com"
GITHUB_WEBHOOK_SECRET="<github webhook secret key>"
```

## 🚀 Steps to Run the App Locally
1. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```
2. Install dependencies
```bash
pip3 install -r requirements.txt
```
3. Run the app
```bash
python3 run_app.py
```

### 📬 Contact
Maintained by [@vamshikarru01](https://github.com/PR-Review-Agent). Feel free to open an issue or contribute.
