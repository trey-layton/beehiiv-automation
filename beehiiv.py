import http.client
import json
import re
import sys


def get_user_config(user_id):
    with open("user_config.json") as config_file:
        config = json.load(config_file)
    return config.get(user_id)


def extract_post_id(beehiiv_url):
    match = re.search(r"/posts/([^/]+)/", beehiiv_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid beehiiv URL: Unable to extract post ID")


def fetch_post_data(beehiiv_api_key, publication_id, post_id):
    conn = http.client.HTTPSConnection("api.beehiiv.com")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {beehiiv_api_key}",
    }

    endpoint = f"/v2/publications/{publication_id}/posts/{post_id}?expand[]=free_web_content&expand[]=premium_web_content"

    conn.request("GET", endpoint, headers=headers)

    res = conn.getresponse()
    if res.status != 200:
        print(f"API request failed with status code {res.status}")
        sys.exit(1)

    data = res.read()

    return json.loads(data.decode("utf-8"))


def main():
    if len(sys.argv) != 2:
        print("Usage: python beehiiv.py <user_id>")
        sys.exit(1)

    user_id = sys.argv[1]
    user_config = get_user_config(user_id)

    if not user_config:
        print(f"User ID '{user_id}' not found in config.")
        sys.exit(1)

    beehiiv_api_key = user_config["beehiiv_api_key"]
    publication_id = user_config["publication_id"]
    beehiiv_url = user_config["beehiiv_url"]

    try:
        post_id = extract_post_id(beehiiv_url)
    except ValueError as e:
        print(e)
        sys.exit(1)

    post_data = fetch_post_data(beehiiv_api_key, publication_id, post_id)

    # Debugging: Print the full response data
    print("Full response data:")
    print(json.dumps(post_data, indent=2))

    post_info = post_data.get("data", {})

    result = {
        "web_url": post_info.get("web_url"),
        "free_web_content": post_info.get("content", {}).get("free", {}).get("web"),
        "premium_web_content": post_info.get("content", {})
        .get("premium", {})
        .get("web"),
        "thumbnail_url": post_info.get("thumbnail_url"),
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
