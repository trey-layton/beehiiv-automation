import sys
import os
import json
from fastapi.testclient import TestClient
from unittest.mock import patch

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from api.main import app
from tests.mocks import (
    mock_verify_token,
    mock_get_user_id,
    mock_load_user_config,
    mock_save_user_config,
    mock_run_main_process,
)

client = TestClient(app)


@patch("core.auth.supabase_auth.verify_token", side_effect=mock_verify_token)
@patch("core.auth.supabase_auth.get_user_id", side_effect=mock_get_user_id)
@patch("core.config.user_config.load_user_config", side_effect=mock_load_user_config)
def test_get_user_config(mock_load, mock_get_id, mock_verify):
    headers = {"Authorization": "Bearer fake_token"}

    response = client.get("/user_config", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "beehiiv_api_key": "test_api_key",
        "subscribe_url": "https://test.subscribe.url",
        "publication_id": "test_publication_id",
    }


@patch("core.auth.supabase_auth.verify_token", side_effect=mock_verify_token)
@patch("core.auth.supabase_auth.get_user_id", side_effect=mock_get_user_id)
@patch("core.config.user_config.save_user_config", side_effect=mock_save_user_config)
def test_update_user_config(mock_save, mock_get_id, mock_verify):
    headers = {"Authorization": "Bearer fake_token"}
    new_config = {
        "beehiiv_api_key": "new_api_key",
        "subscribe_url": "https://new.subscribe.url",
        "publication_id": "new_publication_id",
    }

    response = client.post("/user_config", headers=headers, json=new_config)

    assert response.status_code == 200
    assert response.json() == {"status": "success"}


@patch("core.auth.supabase_auth.verify_token", side_effect=mock_verify_token)
@patch("core.auth.supabase_auth.get_user_id", side_effect=mock_get_user_id)
@patch("core.main_process.run_main_process", side_effect=mock_run_main_process)
def test_generate_content(mock_run, mock_get_id, mock_verify):
    headers = {"Authorization": "Bearer fake_token"}
    params = {
        "edition_url": "https://example.com/newsletter/123",
        "precta_tweet": True,
        "postcta_tweet": True,
        "thread_tweet": False,
        "long_form_tweet": True,
        "linkedin": True,
    }

    response = client.post("/generate_content", headers=headers, json=params)

    assert response.status_code == 200
    content = response.json()
    assert content == {
        "precta_tweet": "This is a pre-CTA tweet",
        "postcta_tweet": "This is a post-CTA tweet",
        "long_form_tweet": "This is a long-form tweet",
        "linkedin": "This is a LinkedIn post",
    }
