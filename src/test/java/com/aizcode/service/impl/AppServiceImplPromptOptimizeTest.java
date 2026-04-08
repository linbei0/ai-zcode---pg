package com.aizcode.service.impl;

import com.aizcode.ai.PromptOptimizerService;
import com.aizcode.ai.PromptOptimizerServiceFactory;
import com.aizcode.exception.BusinessException;
import com.aizcode.exception.ErrorCode;
import com.aizcode.model.dto.app.PromptOptimizeRequest;
import com.aizcode.model.entity.App;
import com.aizcode.model.entity.User;
import com.aizcode.model.vo.PromptOptimizeResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AppServiceImplPromptOptimizeTest {

    @Spy
    @InjectMocks
    private AppServiceImpl appService;

    @Mock
    private PromptOptimizerServiceFactory promptOptimizerServiceFactory;

    @Mock
    private PromptOptimizerService promptOptimizerService;

    @Test
    void optimizePromptShouldRejectBlankPrompt() {
        PromptOptimizeRequest request = new PromptOptimizeRequest();
        request.setPrompt("   ");
        request.setScene("create_app");

        BusinessException exception = assertThrows(BusinessException.class,
                () -> appService.optimizePrompt(request, buildUser(1L)));

        assertEquals(ErrorCode.PARAMS_ERROR.getCode(), exception.getCode());
        verify(promptOptimizerServiceFactory, never()).createPromptOptimizerService();
    }

    @Test
    void optimizePromptShouldUseCreateAppScene() {
        PromptOptimizeRequest request = new PromptOptimizeRequest();
        request.setPrompt("做一个个人博客");
        request.setScene("create_app");
        when(promptOptimizerServiceFactory.createPromptOptimizerService()).thenReturn(promptOptimizerService);
        when(promptOptimizerService.optimizePrompt(contains("做一个个人博客")))
                .thenReturn(buildOptimizeResponse("优化后的创建提示词", "basic"));

        PromptOptimizeResponse response = appService.optimizePrompt(request, buildUser(1L));

        assertEquals("优化后的创建提示词", response.getOptimizedPrompt());
        assertEquals("basic", response.getMode());
    }

    @Test
    void optimizePromptShouldRejectNonOwnerInChatScene() {
        PromptOptimizeRequest request = new PromptOptimizeRequest();
        request.setPrompt("把首页按钮改成蓝色");
        request.setScene("chat");
        request.setAppId(1001L);
        doReturn(App.builder()
                .id(1001L)
                .userId(2L)
                .appName("博客站点")
                .initPrompt("创建一个博客")
                .codeGenType("vue_project")
                .build()).when(appService).getById(1001L);

        BusinessException exception = assertThrows(BusinessException.class,
                () -> appService.optimizePrompt(request, buildUser(1L)));

        assertEquals(ErrorCode.NO_AUTH_ERROR.getCode(), exception.getCode());
        verify(promptOptimizerServiceFactory, never()).createPromptOptimizerService();
    }

    @Test
    void optimizePromptShouldPassAppContextInChatScene() {
        PromptOptimizeRequest request = new PromptOptimizeRequest();
        request.setPrompt("把首页按钮改成蓝色");
        request.setScene("chat");
        request.setAppId(1001L);
        doReturn(App.builder()
                .id(1001L)
                .userId(1L)
                .appName("博客站点")
                .initPrompt("创建一个博客")
                .codeGenType("vue_project")
                .build()).when(appService).getById(1001L);
        when(promptOptimizerServiceFactory.createPromptOptimizerService()).thenReturn(promptOptimizerService);
        when(promptOptimizerService.optimizePrompt(contains("把首页按钮改成蓝色")))
                .thenReturn(buildOptimizeResponse("优化后的修改提示词", "detail"));

        PromptOptimizeResponse response = appService.optimizePrompt(request, buildUser(1L));

        assertEquals("优化后的修改提示词", response.getOptimizedPrompt());
        assertEquals("detail", response.getMode());
    }

    private static User buildUser(Long userId) {
        User user = new User();
        user.setId(userId);
        return user;
    }

    private static PromptOptimizeResponse buildOptimizeResponse(String optimizedPrompt, String mode) {
        PromptOptimizeResponse response = new PromptOptimizeResponse();
        response.setOptimizedPrompt(optimizedPrompt);
        response.setMode(mode);
        return response;
    }
}
