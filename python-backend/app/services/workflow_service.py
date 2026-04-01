from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass

from app.core.exceptions import BusinessException, ErrorCode
from app.services.ai_service import AIGateway
from app.services.storage_service import StorageService


@dataclass
class WorkflowQualityResult:
    isValid: bool
    errors: list[str]
    suggestions: list[str]


@dataclass
class WorkflowContextPayload:
    currentStep: str
    originalPrompt: str
    imageListStr: str | None
    imageList: list[dict]
    enhancedPrompt: str | None
    generationType: str | None
    generatedCodeDir: str | None
    buildResultDir: str | None
    qualityResult: dict | None
    errorMessage: str | None
    imageCollectionPlan: dict | None
    contentImages: list[dict]
    illustrations: list[dict]
    diagrams: list[dict]
    logos: list[dict]


class WorkflowService:
    def __init__(self, ai_gateway: AIGateway, storage_service: StorageService):
        self.ai_gateway = ai_gateway
        self.storage_service = storage_service

    async def execute(self, original_prompt: str) -> dict:
        context = WorkflowContextPayload(
            currentStep="初始化",
            originalPrompt=original_prompt,
            imageListStr=None,
            imageList=[],
            enhancedPrompt=None,
            generationType=None,
            generatedCodeDir=None,
            buildResultDir=None,
            qualityResult=None,
            errorMessage=None,
            imageCollectionPlan=None,
            contentImages=[],
            illustrations=[],
            diagrams=[],
            logos=[],
        )
        context.currentStep = "图片收集"
        context.currentStep = "提示词增强"
        context.enhancedPrompt = original_prompt
        context.currentStep = "路由"
        context.generationType = self.ai_gateway.route_code_type(original_prompt)
        context.currentStep = "代码生成"
        code_chunks: list[str] = []
        async for chunk in self.ai_gateway.stream_generate(context.generationType, original_prompt, ""):
            code_chunks.append(chunk)
        full_content = "".join(code_chunks)
        workflow_id = uuid.uuid4().hex[:8]
        target_dir = self.storage_service.save_generated_code(context.generationType, f"workflow_{workflow_id}", full_content)
        context.generatedCodeDir = str(target_dir)
        context.currentStep = "代码质检"
        quality = self._check_quality(context.generationType, full_content)
        context.qualityResult = asdict(quality)
        if not quality.isValid:
            context.errorMessage = "代码质检失败"
            return asdict(context)
        if context.generationType == "vue_project":
            context.currentStep = "项目构建"
            build_dir = self.storage_service.build_vue_project_if_needed(context.generationType, target_dir)
            context.buildResultDir = str(build_dir) if build_dir else None
        context.currentStep = "完成"
        return asdict(context)

    async def execute_flux(self, original_prompt: str) -> AsyncIterator[str]:
        yield self._format_sse_event(
            "workflow_start",
            {"message": "开始执行代码生成工作流", "originalPrompt": original_prompt},
        )
        step_number = 1
        for step_name in ["图片收集", "提示词增强", "路由", "代码生成", "代码质检", "完成"]:
            yield self._format_sse_event(
                "step_completed",
                {"stepNumber": step_number, "currentStep": step_name},
            )
            step_number += 1
        await self.execute(original_prompt)
        yield self._format_sse_event("workflow_completed", {"message": "代码生成工作流执行完成！"})

    async def execute_sse(self, original_prompt: str) -> AsyncIterator[str]:
        async for item in self.execute_flux(original_prompt):
            yield item

    def _check_quality(self, generation_type: str, content: str) -> WorkflowQualityResult:
        if generation_type == "html" and "<html" not in content.lower():
            return WorkflowQualityResult(False, ["缺少 html 根元素"], ["请补全完整 HTML 文档"])
        if generation_type == "multi_file" and "```html" not in content.lower():
            return WorkflowQualityResult(False, ["缺少 html 代码块"], ["请输出完整的 html/css/js 代码块"])
        if generation_type == "vue_project" and "FILE:" not in content:
            return WorkflowQualityResult(False, ["缺少文件结构"], ["请输出完整的 Vue 工程文件"])
        return WorkflowQualityResult(True, [], [])

    def _format_sse_event(self, event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
