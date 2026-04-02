from app.core.config import build_settings
from app.services.ai_service import (
    build_chat_model_kwargs,
    build_routing_model_settings,
    build_routing_chat_model_kwargs,
    should_disable_thinking_for_model,
)


def test_should_disable_thinking_for_qwen_models() -> None:
    assert should_disable_thinking_for_model("qwen3.5-plus") is True
    assert should_disable_thinking_for_model("qwen-plus") is True
    assert should_disable_thinking_for_model("deepseek-chat") is False


def test_build_chat_model_kwargs_disables_thinking_for_qwen_by_default() -> None:
    settings = build_settings(
        {
            "openai_api_key": "demo-key",
            "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openai_model": "qwen3.5-plus",
        }
    )

    kwargs = build_chat_model_kwargs(settings)

    assert kwargs["extra_body"] == {"enable_thinking": False}


def test_build_chat_model_kwargs_respects_explicit_enable_thinking() -> None:
    settings = build_settings(
        {
            "openai_api_key": "demo-key",
            "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openai_model": "qwen3.5-plus",
            "openai_enable_thinking": True,
        }
    )

    kwargs = build_chat_model_kwargs(settings)

    assert "extra_body" not in kwargs


def test_build_routing_chat_model_kwargs_still_disables_thinking_for_qwen() -> None:
    settings = build_settings(
        {
            "openai_api_key": "demo-key",
            "openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openai_model": "qwen3.5-plus",
            "openai_enable_thinking": True,
        }
    )

    kwargs = build_routing_chat_model_kwargs(settings)

    assert kwargs["extra_body"] == {"enable_thinking": False}


def test_build_routing_model_settings_prefers_dedicated_routing_model() -> None:
    settings = build_settings(
        {
            "openai_api_key": "main-key",
            "openai_base_url": "https://main.example.com/v1",
            "openai_model": "deepseek-chat",
            "routing_openai_api_key": "routing-key",
            "routing_openai_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "routing_openai_model": "qwen-plus",
        }
    )

    routing_settings = build_routing_model_settings(settings)
    kwargs = build_routing_chat_model_kwargs(settings)

    assert routing_settings["api_key"] == "routing-key"
    assert routing_settings["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert routing_settings["model"] == "qwen-plus"
    assert kwargs["extra_body"] == {"enable_thinking": False}
