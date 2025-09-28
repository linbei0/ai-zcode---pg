package com.aizcode.service;

public interface ScreenshotService {
    /**
     * 截取网页截图并上传
     * @param webUrl
     * @return
     */
    String generateAndUploadScreenshot(String webUrl);
}
