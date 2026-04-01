from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.ai.prompts import (
    HTML_SYSTEM_PROMPT,
    MULTI_FILE_SYSTEM_PROMPT,
    ROUTING_SYSTEM_PROMPT,
    VUE_PROJECT_SYSTEM_PROMPT,
)
from app.core.config import Settings
from app.core.exceptions import BusinessException, ErrorCode

CodeGenType = Literal["html", "multi_file", "vue_project"]


class CodeTypeDecision(BaseModel):
    code_gen_type: CodeGenType


class AIGateway(ABC):
    @abstractmethod
    def route_code_type(self, init_prompt: str) -> CodeGenType: ...

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
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        )

    def route_code_type(self, init_prompt: str) -> CodeGenType:
        prompt = ChatPromptTemplate.from_messages(
            [("system", ROUTING_SYSTEM_PROMPT), ("human", "{init_prompt}")]
        )
        structured_llm = self.llm.with_structured_output(
            CodeTypeDecision,
            method="function_calling",
        )
        decision = (prompt | structured_llm).invoke({"init_prompt": init_prompt})
        return decision.code_gen_type

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
