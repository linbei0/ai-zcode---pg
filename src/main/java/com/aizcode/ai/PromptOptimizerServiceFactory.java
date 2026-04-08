package com.aizcode.ai;

import com.aizcode.utils.SpringContextUtil;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.service.AiServices;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 提示词优化服务工厂
 */
@Slf4j
@Configuration
public class PromptOptimizerServiceFactory {

    /**
     * 创建提示词优化服务实例
     */
    public PromptOptimizerService createPromptOptimizerService() {
        ChatModel chatModel = SpringContextUtil.getBean("routingChatModelPrototype", ChatModel.class);
        return AiServices.builder(PromptOptimizerService.class)
                .chatModel(chatModel)
                .build();
    }

    /**
     * 默认 Bean
     */
    @Bean
    public PromptOptimizerService promptOptimizerService() {
        return createPromptOptimizerService();
    }
}
