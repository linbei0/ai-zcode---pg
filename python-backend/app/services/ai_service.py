from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.ai.prompts import (
    HTML_SYSTEM_PROMPT,
    MULTI_FILE_SYSTEM_PROMPT,
    PROMPT_OPTIMIZER_SYSTEM_PROMPT,
    ROUTING_SYSTEM_PROMPT,
    VUE_PROJECT_SYSTEM_PROMPT,
)
from app.core.config import Settings
from app.core.exceptions import BusinessException, ErrorCode
from app.schemas.app import PromptOptimizeMode, PromptOptimizeScene

CodeGenType = Literal["html", "multi_file", "vue_project"]


class CodeTypeDecision(BaseModel):
    code_gen_type: CodeGenType


class PromptOptimizationResult(BaseModel):
    optimized_prompt: str
    mode: PromptOptimizeMode


def build_prompt_optimizer_context(scene: PromptOptimizeScene, app_context: dict[str, Any] | None = None) -> str:
    if scene == "create_app":
        return "当前场景：创建新应用。请把用户想法整理成适合 AI-ZCode 首次生成网站/页面/工程的输入。"

    if not app_context:
        return "当前场景：修改现有应用。请聚焦本次改动，不要把需求扩展成整站重做。"

    app_name = app_context.get("appName") or "未命名应用"
    init_prompt = app_context.get("initPrompt") or "未提供"
    code_gen_type = app_context.get("codeGenType") or "未提供"
    return (
        "当前场景：修改现有应用。请聚焦增量修改，不要重写整个项目。\n"
        f"当前应用：{app_name}\n"
        f"初始需求：{init_prompt}\n"
        f"代码生成类型：{code_gen_type}"
    )


def should_disable_thinking_for_model(model_name: str) -> bool:
    normalized_model_name = model_name.strip().lower()
    return normalized_model_name.startswith("qwen")


def build_chat_model_kwargs(settings: Settings) -> dict:
    chat_model_kwargs = {
        "api_key": settings.openai_api_key,
        "base_url": settings.openai_base_url,
        "model": settings.openai_model,
    }
    if settings.openai_enable_thinking is False:
        chat_model_kwargs["extra_body"] = {"enable_thinking": False}
    elif settings.openai_enable_thinking is None and should_disable_thinking_for_model(settings.openai_model):
        chat_model_kwargs["extra_body"] = {"enable_thinking": False}
    return chat_model_kwargs


def build_routing_model_settings(settings: Settings) -> dict:
    return {
        "api_key": settings.routing_openai_api_key or settings.openai_api_key,
        "base_url": settings.routing_openai_base_url or settings.openai_base_url,
        "model": settings.routing_openai_model or settings.openai_model,
        "enable_thinking": settings.routing_openai_enable_thinking,
    }


def build_routing_chat_model_kwargs(settings: Settings) -> dict:
    routing_settings = build_routing_model_settings(settings)
    chat_model_kwargs = {
        "api_key": routing_settings["api_key"],
        "base_url": routing_settings["base_url"],
        "model": routing_settings["model"],
    }
    if routing_settings["enable_thinking"] is False:
        chat_model_kwargs["extra_body"] = {"enable_thinking": False}
    elif (
        routing_settings["enable_thinking"] is None
        and should_disable_thinking_for_model(routing_settings["model"])
    ):
        chat_model_kwargs["extra_body"] = {"enable_thinking": False}
    return chat_model_kwargs


class AIGateway(ABC):
    @abstractmethod
    def route_code_type(self, init_prompt: str) -> CodeGenType: ...

    @abstractmethod
    def optimize_prompt(
        self,
        prompt: str,
        scene: PromptOptimizeScene,
        app_context: dict[str, Any] | None = None,
    ) -> dict[str, str]: ...

    @abstractmethod
    async def stream_generate(
        self,
        code_gen_type: CodeGenType,
        user_message: str,
        history_text: str,
    ) -> AsyncIterator[str]: ...


class TestingAIGateway(AIGateway):
    def route_code_type(self, init_prompt: str) -> CodeGenType:
        lower = init_prompt.lower()
        if "vue" in lower:
            return "vue_project"
        if "js" in lower or "javascript" in lower or "交互" in init_prompt:
            return "multi_file"
        return "html"

    def optimize_prompt(
        self,
        prompt: str,
        scene: PromptOptimizeScene,
        app_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        normalized_prompt = prompt.strip()
        if scene == "create_app":
            return {
                "optimizedPrompt": (
                    f"请围绕以下需求生成应用，并明确产品类型、核心页面、关键功能、视觉风格、"
                    f"响应式要求与目标用户：{normalized_prompt}"
                ),
                "mode": "basic",
            }

        context_text = build_prompt_optimizer_context(scene, app_context)
        return {
            "optimizedPrompt": (
                f"{context_text}\n请仅在当前应用基础上完成以下修改，说明影响范围、保留不变部分、"
                f"UI/交互/文案/样式约束：{normalized_prompt}"
            ),
            "mode": "detail",
        }

    async def stream_generate(
        self,
        code_gen_type: CodeGenType,
        user_message: str,
        history_text: str,
    ) -> AsyncIterator[str]:
        if code_gen_type == "html":
            content = """```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI ZCode</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 40px; background: #f8fafc; }
    .card { max-width: 480px; margin: 0 auto; background: white; padding: 32px; border-radius: 16px; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.1); }
    button { border: none; padding: 12px 18px; border-radius: 999px; background: #2563eb; color: white; }
  </style>
</head>
<body>
  <div class="card">
    <h1>AI 生成页面</h1>
    <p>需求：%s</p>
    <button>立即体验</button>
  </div>
</body>
</html>
```""" % user_message
        elif code_gen_type == "multi_file":
            content = """```html
<!DOCTYPE html>
<html><head><link rel="stylesheet" href="style.css" /></head><body><h1 id="title">Hello</h1><script src="script.js"></script></body></html>
```
```css
body { font-family: sans-serif; background: #f5f7fb; }
```
```javascript
document.getElementById('title').textContent = 'Hello AI-ZCode';
```"""
        else:
            content = """FILE: package.json
```json
{"name":"ai-zcode-vue","private":true,"version":"0.0.0","type":"module","scripts":{"dev":"vite","build":"vite build"},"dependencies":{"vue":"^3.5.0"},"devDependencies":{"vite":"^7.0.0","@vitejs/plugin-vue":"^6.0.0"}}
```
FILE: index.html
```html
<!DOCTYPE html><html><body><div id="app"></div><script type="module" src="/src/main.js"></script></body></html>
```
FILE: vite.config.js
```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
export default defineConfig({ plugins: [vue()] })
```
FILE: src/main.js
```javascript
import { createApp } from 'vue'
import App from './App.vue'
createApp(App).mount('#app')
```
FILE: src/App.vue
```vue
<template><main><h1>AI ZCode Vue Project</h1><p>%s</p></main></template>
<style>body{font-family:Arial,sans-serif;background:#f8fafc}main{max-width:720px;margin:80px auto;padding:32px;background:#fff;border-radius:16px}</style>
```""" % user_message
        for chunk in [content[i : i + 80] for i in range(0, len(content), 80)]:
            yield chunk


class LangChainAIGateway(AIGateway):
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise BusinessException(ErrorCode.SYSTEM_ERROR, "未配置 OPENAI_API_KEY，无法启用 Python AI 能力")
        self.llm = ChatOpenAI(**build_chat_model_kwargs(settings))
        self.routing_llm = ChatOpenAI(**build_routing_chat_model_kwargs(settings))

    def route_code_type(self, init_prompt: str) -> CodeGenType:
        prompt = ChatPromptTemplate.from_messages(
            [("system", ROUTING_SYSTEM_PROMPT), ("human", "{init_prompt}")]
        )
        structured_llm = self.routing_llm.with_structured_output(
            CodeTypeDecision,
            method="function_calling",
        )
        decision = (prompt | structured_llm).invoke({"init_prompt": init_prompt})
        return decision.code_gen_type

    def optimize_prompt(
        self,
        prompt: str,
        scene: PromptOptimizeScene,
        app_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        structured_llm = self.routing_llm.with_structured_output(
            PromptOptimizationResult,
            method="function_calling",
        )
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", PROMPT_OPTIMIZER_SYSTEM_PROMPT),
                (
                    "human",
                    "场景：{scene}\n"
                    "隐藏上下文：\n{optimizer_context}\n\n"
                    "用户原始需求：\n{prompt}\n\n"
                    "请返回结构化结果。",
                ),
            ]
        )
        result = (prompt_template | structured_llm).invoke(
            {
                "scene": scene,
                "optimizer_context": build_prompt_optimizer_context(scene, app_context),
                "prompt": prompt,
            }
        )
        return {
            "optimizedPrompt": result.optimized_prompt.strip(),
            "mode": result.mode,
        }

    async def stream_generate(
        self,
        code_gen_type: CodeGenType,
        user_message: str,
        history_text: str,
    ) -> AsyncIterator[str]:
        system_prompt = {
            "html": HTML_SYSTEM_PROMPT,
            "multi_file": MULTI_FILE_SYSTEM_PROMPT,
            "vue_project": VUE_PROJECT_SYSTEM_PROMPT,
        }[code_gen_type]
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "历史上下文：\n{history_text}\n\n当前需求：\n{user_message}"),
            ]
        )
        chain = prompt | self.llm | StrOutputParser()
        async for chunk in chain.astream({"user_message": user_message, "history_text": history_text}):
            yield chunk


class DisabledAIGateway(AIGateway):
    def route_code_type(self, init_prompt: str) -> CodeGenType:
        raise BusinessException(ErrorCode.SYSTEM_ERROR, "未配置 OPENAI_API_KEY，无法启用 Python AI 能力")

    def optimize_prompt(
        self,
        prompt: str,
        scene: PromptOptimizeScene,
        app_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        raise BusinessException(ErrorCode.SYSTEM_ERROR, "未配置 OPENAI_API_KEY，无法启用 Python AI 能力")

    async def stream_generate(
        self,
        code_gen_type: CodeGenType,
        user_message: str,
        history_text: str,
    ) -> AsyncIterator[str]:
        raise BusinessException(ErrorCode.SYSTEM_ERROR, "未配置 OPENAI_API_KEY，无法启用 Python AI 能力")
        yield ""


def build_ai_gateway(settings: Settings) -> AIGateway:
    if settings.testing:
        return TestingAIGateway()
    if not settings.openai_api_key:
        return DisabledAIGateway()
    return LangChainAIGateway(settings)
