-- 数据库初始化 (PostgreSQL版本)

-- 创建数据库
CREATE DATABASE ai_zcode;

-- 连接到数据库
\c ai_zcode;

-- 用户表
-- 以下是建表语句

-- 用户表
CREATE TABLE IF NOT EXISTS "user" (
    id            BIGSERIAL PRIMARY KEY,
    user_account  VARCHAR(256) NOT NULL,
    user_password VARCHAR(512) NOT NULL,
    user_name     VARCHAR(256),
    user_avatar   VARCHAR(1024),
    user_profile  VARCHAR(512),
    user_role     VARCHAR(256) DEFAULT 'user' NOT NULL,
    edit_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_delete     SMALLINT DEFAULT 0 NOT NULL
);

-- 用户表注释
COMMENT ON TABLE "user" IS '用户';
COMMENT ON COLUMN "user".id IS 'id';
COMMENT ON COLUMN "user".user_account IS '账号';
COMMENT ON COLUMN "user".user_password IS '密码';
COMMENT ON COLUMN "user".user_name IS '用户昵称';
COMMENT ON COLUMN "user".user_avatar IS '用户头像';
COMMENT ON COLUMN "user".user_profile IS '用户简介';
COMMENT ON COLUMN "user".user_role IS '用户角色：user/admin';
COMMENT ON COLUMN "user".edit_time IS '编辑时间';
COMMENT ON COLUMN "user".create_time IS '创建时间';
COMMENT ON COLUMN "user".update_time IS '更新时间';
COMMENT ON COLUMN "user".is_delete IS '是否删除';

-- 用户表索引和约束
ALTER TABLE "user" ADD CONSTRAINT uk_userAccount UNIQUE (user_account);
CREATE INDEX idx_userName ON "user" (user_name);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_time_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表创建更新时间触发器
CREATE TRIGGER update_user_updateTime BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_time_column();

-- 应用表
CREATE TABLE app (
    id            BIGSERIAL PRIMARY KEY,
    app_name      VARCHAR(256),
    cover         VARCHAR(512),
    init_prompt   TEXT,
    code_gen_type VARCHAR(64),
    deploy_key    VARCHAR(64),
    deployed_time TIMESTAMP,
    priority      INTEGER DEFAULT 0 NOT NULL,
    user_id       BIGINT NOT NULL,
    edit_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    create_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time   TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_delete     SMALLINT DEFAULT 0 NOT NULL
);

-- 应用表注释
COMMENT ON TABLE app IS '应用';
COMMENT ON COLUMN app.id IS 'id';
COMMENT ON COLUMN app.app_name IS '应用名称';
COMMENT ON COLUMN app.cover IS '应用封面';
COMMENT ON COLUMN app.init_prompt IS '应用初始化的 prompt';
COMMENT ON COLUMN app.code_gen_type IS '代码生成类型（枚举）';
COMMENT ON COLUMN app.deploy_key IS '部署标识';
COMMENT ON COLUMN app.deployed_time IS '部署时间';
COMMENT ON COLUMN app.priority IS '优先级';
COMMENT ON COLUMN app.user_id IS '创建用户id';
COMMENT ON COLUMN app.edit_time IS '编辑时间';
COMMENT ON COLUMN app.create_time IS '创建时间';
COMMENT ON COLUMN app.update_time IS '更新时间';
COMMENT ON COLUMN app.is_delete IS '是否删除';

-- 应用表索引和约束
ALTER TABLE app ADD CONSTRAINT uk_deployKey UNIQUE (deploy_key);
CREATE INDEX idx_appName ON app (app_name);
CREATE INDEX idx_userId ON app (user_id);

-- 为应用表创建更新时间触发器
CREATE TRIGGER update_app_updateTime BEFORE UPDATE ON app
    FOR EACH ROW EXECUTE FUNCTION update_updated_time_column();

-- 对话历史表
CREATE TABLE chat_history (
    id           BIGSERIAL PRIMARY KEY,
    message      TEXT NOT NULL,
    message_type VARCHAR(32) NOT NULL,
    app_id       BIGINT NOT NULL,
    user_id      BIGINT NOT NULL,
    create_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    update_time  TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_delete    SMALLINT DEFAULT 0 NOT NULL
);

-- 对话历史表注释
COMMENT ON TABLE chat_history IS '对话历史';
COMMENT ON COLUMN chat_history.id IS 'id';
COMMENT ON COLUMN chat_history.message IS '消息';
COMMENT ON COLUMN chat_history.message_type IS 'user/ai';
COMMENT ON COLUMN chat_history.app_id IS '应用id';
COMMENT ON COLUMN chat_history.user_id IS '创建用户id';
COMMENT ON COLUMN chat_history.create_time IS '创建时间';
COMMENT ON COLUMN chat_history.update_time IS '更新时间';
COMMENT ON COLUMN chat_history.is_delete IS '是否删除';

-- 对话历史表索引
CREATE INDEX idx_appId ON chat_history (app_id);
CREATE INDEX idx_createTime ON chat_history (create_time);
CREATE INDEX idx_appId_createTime ON chat_history (app_id, create_time);

-- 为对话历史表创建更新时间触发器
CREATE TRIGGER update_chat_history_updateTime BEFORE UPDATE ON chat_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_time_column();

-- 添加外键约束（可选）
-- ALTER TABLE app ADD CONSTRAINT fk_app_userId FOREIGN KEY (user_id) REFERENCES "user"(id);
-- ALTER TABLE chat_history ADD CONSTRAINT fk_chat_history_appId FOREIGN KEY (app_id) REFERENCES app(id);
-- ALTER TABLE chat_history ADD CONSTRAINT fk_chat_history_userId FOREIGN KEY (user_id) REFERENCES "user"(id);