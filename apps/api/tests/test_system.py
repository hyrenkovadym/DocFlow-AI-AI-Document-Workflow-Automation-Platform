def test_system_info_exposes_safe_runtime_configuration(client):
    response = client.get("/api/system/info")
    assert response.status_code == 200
    payload = response.json()

    assert payload["processing_mode"] in {"sync", "async"}
    assert payload["ai_provider"] in {"mock", "openai"}
    assert isinstance(payload["app_env"], str)
    assert isinstance(payload["version"], str)
    assert payload["docs_url"] == "/docs"
    assert payload["openapi_url"] == "/openapi.json"

    forbidden_keys = {
        "openai_api_key",
        "secret_key",
        "database_url",
        "redis_url",
        "jwt_secret",
        "jwt_token",
    }
    for key in forbidden_keys:
        assert key not in payload


def test_ready_endpoint_includes_dependency_status(client):
    response = client.get("/api/ready")
    assert response.status_code in {200, 503}
    payload = response.json()

    assert payload["status"] in {"ready", "degraded"}
    assert "dependencies" in payload
    assert "database" in payload["dependencies"]
    assert isinstance(payload["dependencies"]["database"]["ok"], bool)
    assert "redis" in payload["dependencies"]
    assert isinstance(payload["dependencies"]["redis"]["ok"], bool)
    assert payload["processing_mode"] in {"sync", "async"}
    assert payload["ai_provider"] in {"mock", "openai"}
