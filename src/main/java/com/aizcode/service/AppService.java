package com.aizcode.service;

import com.aizcode.model.dto.app.AppQueryRequest;
import com.aizcode.model.entity.User;
import com.aizcode.model.vo.AppVO;
import com.mybatisflex.core.query.QueryWrapper;
import com.mybatisflex.core.service.IService;
import com.aizcode.model.entity.App;
import reactor.core.publisher.Flux;

import java.util.List;

/**
 *  服务层。
 *
 * @author jiang
 */
public interface AppService extends IService<App> {
    /**
     * 获取应用脱敏数据
     * @param app
     * @return
     */
    AppVO getAppVO(App app);

    /**
     * 获取查询包装类
     * @param appQueryRequest
     * @return
     */
    QueryWrapper getQueryWrapper(AppQueryRequest appQueryRequest);

    /**
     * 获取应用列表
     * @param appList
     * @return
     */
    List<AppVO> getAppVOList(List<App> appList);

    /**
     * 生成代码
     * @param appId
     * @param message
     * @param loginUser
     * @return
     */
    Flux<String> chatToGenCode(Long appId, String message, User loginUser);

    /**
     * 部署应用
     * @param appId
     * @param loginUser
     * @return
     */
    String deployApp(Long appId, User loginUser);

    /**
     * 异步生成应用截图
     * @param appId
     * @param appUrl
     */
    void generateAppScreenshotAsync(Long appId, String appUrl);
}
