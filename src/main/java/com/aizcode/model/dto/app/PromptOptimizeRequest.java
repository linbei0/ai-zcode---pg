package com.aizcode.model.dto.app;

import lombok.Data;

import java.io.Serializable;

@Data
public class PromptOptimizeRequest implements Serializable {

    /**
     * 原始提示词
     */
    private String prompt;

    /**
     * 场景：create_app / chat
     */
    private String scene;

    /**
     * 聊天场景下的应用 ID
     */
    private Long appId;

    private static final long serialVersionUID = 1L;
}
