package com.aizcode.controller;

import com.aizcode.common.BaseResponse;
import com.aizcode.model.dto.app.PromptOptimizeRequest;
import com.aizcode.model.entity.User;
import com.aizcode.model.vo.PromptOptimizeResponse;
import com.aizcode.ratelimiter.annotation.RateLimit;
import com.aizcode.ratelimiter.enums.RateLimitType;
import com.aizcode.service.AppService;
import com.aizcode.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.lang.reflect.Method;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class AppControllerPromptOptimizeTest {

    @InjectMocks
    private AppController appController;

    @Mock
    private AppService appService;

    @Mock
    private UserService userService;

    @Mock
    private HttpServletRequest request;

    @Test
    void optimizePromptShouldReturnSuccessResponse() {
        PromptOptimizeRequest promptOptimizeRequest = new PromptOptimizeRequest();
        promptOptimizeRequest.setPrompt("做一个个人博客");
        promptOptimizeRequest.setScene("create_app");
        User loginUser = new User();
        loginUser.setId(1L);
        PromptOptimizeResponse serviceResponse = new PromptOptimizeResponse();
        serviceResponse.setOptimizedPrompt("优化后的提示词");
        serviceResponse.setMode("basic");
        when(userService.getLoginUser(request)).thenReturn(loginUser);
        when(appService.optimizePrompt(promptOptimizeRequest, loginUser)).thenReturn(serviceResponse);

        BaseResponse<PromptOptimizeResponse> response = appController.optimizePrompt(promptOptimizeRequest, request);

        assertEquals(0, response.getCode());
        assertNotNull(response.getData());
        assertEquals("优化后的提示词", response.getData().getOptimizedPrompt());
        assertEquals("basic", response.getData().getMode());
        verify(appService).optimizePrompt(promptOptimizeRequest, loginUser);
    }

    @Test
    void optimizePromptShouldHaveIndependentRateLimit() throws NoSuchMethodException {
        Method method = AppController.class.getMethod("optimizePrompt", PromptOptimizeRequest.class, HttpServletRequest.class);
        RateLimit rateLimit = method.getAnnotation(RateLimit.class);

        assertNotNull(rateLimit);
        assertEquals(RateLimitType.USER, rateLimit.limitType());
        assertEquals(10, rateLimit.rate());
        assertEquals(60, rateLimit.rateInterval());
    }
}
