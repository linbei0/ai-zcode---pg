package com.aizcode.service;

import com.aizcode.model.dto.app.AppQueryRequest;
import com.aizcode.model.vo.AppVO;
import com.mybatisflex.core.query.QueryWrapper;
import com.mybatisflex.core.service.IService;
import com.aizcode.model.entity.App;

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
}
