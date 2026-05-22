def test_system_info_exposes_safe_runtime_configuration(client):
    response = client.get("/api/system/info")
    assert response.status_code == 200
    payload = response.json()

    assert payload["processing_mode"] in {"sync", "async"}
    assert payload["ai_provider"] in {"mock", "openai"}
    assert isinstance(payload["app_env"], str)
    assert "openai_api_key" not in payload
