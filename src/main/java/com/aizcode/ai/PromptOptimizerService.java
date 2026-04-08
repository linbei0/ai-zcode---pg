package com.aizcode.ai;

import com.aizcode.model.vo.PromptOptimizeResponse;
import dev.langchain4j.service.SystemMessage;
import dev.langchain4j.service.UserMessage;

/**
 * 提示词优化服务
 */
public interface PromptOptimizerService {

    /**
     * 优化用户提示词，返回结构化结果
     *
     * @param userMessage 组装后的用户消息
     * @return 优化结果
     */
    @SystemMessage(fromResource = "prompt/prompt-optimizer-system-prompt.txt")
    PromptOptimizeResponse optimizePrompt(@UserMessage String userMessage);
}
