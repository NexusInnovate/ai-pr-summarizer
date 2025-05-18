from openai import OpenAI
import os
import httpx

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))

def summarize_diff(diff_text):
    prompt = f"Summarize this GitHub PR diff:\n{diff_text[:10000]}"  # Truncate if needed

    response = client.responses.create(
        model="gpt-4o",
        instructions="You're a senior engineer summarizing GitHub PRs in couple of sentences for functional team purpose, Be concise and helpful.",
        input=prompt,
    )
    return response.output_text

def summarize_all_prs(diff_text):
    prompt = f"Summarize this GitHub PR diff:\n{diff_text[:40000]}"  # Truncate if needed

    response = client.responses.create(
        model="gpt-4o",
        instructions="You're a senior engineer summarizing all PR summaries into a release notes in bullet points for manager purpose, Be concise and helpful.",
        input=prompt,
    )
    return response.output_text

def review_pr(diff_text):
    prompt = f"""
        Your task:
        - Identify code quality issues (style, structure, edge cases, security, etc.)
        - Give specific improvement suggestions
        - Include example fixes if possible
        - Be concise and write in couple of sentences

        PR diff:\n{diff_text}
        """

    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a lead software engineer. Review the following GitHub PR diff.",
        input=prompt,
    )
    # print(response.output_text)
    return response.output_text
