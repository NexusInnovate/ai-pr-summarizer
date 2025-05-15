from openai import OpenAI
import os
import httpx

api_key = os.getenv("OPENAI_API_KEY")

def summarize_diff(diff_text):
    prompt = f"Summarize this GitHub PR diff:\n{diff_text[:4000]}"  # Truncate if needed
    client = OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))

    response = client.responses.create(
        model="gpt-4o",
        instructions="You're a senior engineer summarizing GitHub PRs in couple of sentences, Be concise and helpful.",
        input=prompt,
    )
    # print(response.output_text)
    return response.output_text

def review_pr(diff_text):
    prompt = f"""
        Your task:
        - Identify code quality issues (style, structure, edge cases, security, etc.)
        - Give specific improvement suggestions
        - Include example fixes if possible
        - Be concise and helpful

        PR diff:\n{diff_text}
        """
    client = OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))

    response = client.responses.create(
        model="gpt-4o",
        instructions="You are a lead software engineer. Review the following GitHub PR diff.",
        input=prompt,
    )
    # print(response.output_text)
    return response.output_text
