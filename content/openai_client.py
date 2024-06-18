import openai


def setup_openai(api_key):
    openai.api_key = api_key
    return openai


def call_openai(api_key, system_message, user_message):
    client = setup_openai(api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message["content"]},
            {"role": "user", "content": user_message["content"]},
        ],
        max_tokens=280,
        n=1,
        temperature=0.3,
    )
    return response.choices[0].message.content
