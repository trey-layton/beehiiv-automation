# tests/mocks.py


def mock_verify_token(token):
    if token == "fake_token":
        return {"id": "test_user_id"}
    raise Exception("Invalid token")


def mock_get_user_id(token):
    return "test_user_id"


def mock_load_user_config(account_id):
    return {
        "beehiiv_api_key": "test_api_key",
        "subscribe_url": "https://test.subscribe.url",
        "publication_id": "test_publication_id",
    }


def mock_save_user_config(config, account_id):
    return True


async def mock_run_main_process(
    user_id,
    edition_url,
    precta_tweet,
    postcta_tweet,
    thread_tweet,
    long_form_tweet,
    linkedin,
):
    content = {}
    if precta_tweet:
        content["precta_tweet"] = "This is a pre-CTA tweet"
    if postcta_tweet:
        content["postcta_tweet"] = "This is a post-CTA tweet"
    if thread_tweet:
        content["thread_tweet"] = ["This is tweet 1", "This is tweet 2"]
    if long_form_tweet:
        content["long_form_tweet"] = "This is a long-form tweet"
    if linkedin:
        content["linkedin"] = "This is a LinkedIn post"
    return True, "Content generated successfully", content
