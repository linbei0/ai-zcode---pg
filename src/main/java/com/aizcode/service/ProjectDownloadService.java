package com.aizcode.service;

import jakarta.servlet.http.HttpServletResponse;

public interface ProjectDownloadService {
    /**
     * 下载项目源代码
     * @param projectPath
     * @param downloadFileName
     * @param response
     */
    void downloadProjectAsZip(String projectPath, String downloadFileName, HttpServletResponse response);
}
