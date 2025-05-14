from openai import OpenAI
import os
import httpx

api_key = os.getenv("OPENAI_API_KEY")

def summarize_diff(diff_text):
    prompt = f"Summarize this GitHub PR diff:\n{diff_text[:4000]}"  # Truncate if needed
    client = OpenAI(api_key=api_key, http_client=httpx.Client(verify=False))

    response = client.responses.create(
        model="gpt-4o",
        instructions="You're a senior engineer summarizing GitHub PRs.",
        input=prompt,
    )

    print(response.output_text)
    return response.output_text
