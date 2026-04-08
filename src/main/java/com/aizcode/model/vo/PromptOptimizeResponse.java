package com.aizcode.model.vo;

import lombok.Data;

import java.io.Serializable;

@Data
public class PromptOptimizeResponse implements Serializable {

    /**
     * 优化后的提示词
     */
    private String optimizedPrompt;

    /**
     * 优化模式：basic / detail
     */
    private String mode;

    private static final long serialVersionUID = 1L;
}
