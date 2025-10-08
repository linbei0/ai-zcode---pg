# MySQL 到 PostgreSQL 数据库迁移指南

## 概述

本文档详细说明了将 AI-ZCode 项目的数据库从 MySQL 迁移到 PostgreSQL 的过程，包括语法转换的原因、具体变更内容以及后续操作步骤。

## 文件说明

- **原始文件**: `create_table.sql` (MySQL版本)
- **新文件**: `create_table_postgresql.sql` (PostgreSQL版本)

## 主要语法转换说明

### 1. 数据库创建和连接

**MySQL:**
```sql
create database if not exists ai_zcode;
use ai_zcode;
```

**PostgreSQL:**
```sql
CREATE DATABASE ai_zcode;
\c ai_zcode;
```

**转换原因:**
- PostgreSQL 使用 `\c` 命令连接数据库，而不是 `USE` 语句
- PostgreSQL 对大小写更敏感，建议使用大写关键字

### 2. 自增主键

**MySQL:**
```sql
id bigint auto_increment comment 'id' primary key
```

**PostgreSQL:**
```sql
id BIGSERIAL PRIMARY KEY
```

**转换原因:**
- PostgreSQL 使用 `BIGSERIAL` 类型替代 `BIGINT AUTO_INCREMENT`
- `BIGSERIAL` 自动创建序列并设置默认值

### 3. 数据类型转换

| MySQL | PostgreSQL | 转换原因 |
|-------|------------|----------|
| `TINYINT` | `SMALLINT` | PostgreSQL 没有 TINYINT 类型 |
| `DATETIME` | `TIMESTAMP` | PostgreSQL 推荐使用 TIMESTAMP |
| `INT` | `INTEGER` | 更明确的类型声明 |

### 4. 注释处理

**MySQL:**
```sql
create table user (...) comment '用户';
id bigint comment 'id'
```

**PostgreSQL:**
```sql
COMMENT ON TABLE "user" IS '用户';
COMMENT ON COLUMN "user".id IS 'id';
```

**转换原因:**
- PostgreSQL 不支持在 CREATE TABLE 语句中直接添加注释
- 需要使用 `COMMENT ON` 语句单独添加注释

### 5. 表名处理

**MySQL:**
```sql
create table user (...)
```

**PostgreSQL:**
```sql
CREATE TABLE IF NOT EXISTS "user" (...)
```

**转换原因:**
- `user` 是 PostgreSQL 的保留字，需要用双引号包围
- 避免与系统表名冲突

### 6. 索引创建

**MySQL:**
```sql
UNIQUE KEY uk_userAccount (userAccount),
INDEX idx_userName (userName)
```

**PostgreSQL:**
```sql
ALTER TABLE "user" ADD CONSTRAINT uk_userAccount UNIQUE (userAccount);
CREATE INDEX idx_userName ON "user" (userName);
```

**转换原因:**
- PostgreSQL 不支持在 CREATE TABLE 中直接创建命名索引
- 需要使用 ALTER TABLE 或 CREATE INDEX 语句

### 7. 字符集处理

**MySQL:**
```sql
collate = utf8mb4_unicode_ci
```

**PostgreSQL:**
```sql
-- 不需要显式指定，PostgreSQL 默认支持 UTF-8
```

**转换原因:**
- PostgreSQL 默认使用 UTF-8 编码
- 不需要显式指定字符集和排序规则

### 8. 自动更新时间戳

**MySQL:**
```sql
updateTime datetime default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP
```

**PostgreSQL:**
```sql
updateTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL

-- 需要创建触发器函数
CREATE OR REPLACE FUNCTION update_updated_time_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updateTime = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为每个表创建触发器
CREATE TRIGGER update_user_updateTime BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_time_column();
```

**转换原因:**
- PostgreSQL 不支持 `ON UPDATE CURRENT_TIMESTAMP`
- 需要使用触发器实现自动更新时间戳功能

### 9. 驼峰命名字段处理 ⚠️ **重要** (已更新为下划线命名)

**问题描述:**
- PostgreSQL 默认将所有标识符转换为小写
- 驼峰命名的字段在 PostgreSQL 中会变成 `messagetype`、`appid`、`userid`
- 这导致了 `字段 "messageType" 不存在` 的错误

**最终解决方案:**
采用下划线命名约定，避免大小写问题：

**MySQL (原始):**
```sql
messageType VARCHAR(32) NOT NULL,
appId BIGINT NOT NULL,
userId BIGINT NOT NULL,
userAccount VARCHAR(256) NOT NULL,
createTime DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
```

**PostgreSQL (最终版本):**
```sql
message_type VARCHAR(32) NOT NULL,
app_id BIGINT NOT NULL,
user_id BIGINT NOT NULL,
user_account VARCHAR(256) NOT NULL,
create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
```

**字段名映射表:**
| 原MySQL字段名 | 新PostgreSQL字段名 | 说明 |
|--------------|------------------|------|
| `userAccount` | `user_account` | 用户账号 |
| `userPassword` | `user_password` | 用户密码 |
| `userName` | `user_name` | 用户昵称 |
| `userAvatar` | `user_avatar` | 用户头像 |
| `userProfile` | `user_profile` | 用户简介 |
| `userRole` | `user_role` | 用户角色 |
| `appName` | `app_name` | 应用名称 |
| `initPrompt` | `init_prompt` | 初始化提示 |
| `codeGenType` | `code_gen_type` | 代码生成类型 |
| `deployKey` | `deploy_key` | 部署标识 |
| `deployedTime` | `deployed_time` | 部署时间 |
| `userId` | `user_id` | 用户ID |
| `messageType` | `message_type` | 消息类型 |
| `appId` | `app_id` | 应用ID |
| `createTime` | `create_time` | 创建时间 |
| `updateTime` | `update_time` | 更新时间 |
| `editTime` | `edit_time` | 编辑时间 |
| `isDelete` | `is_delete` | 删除标记 |

**优势:**
- 避免了PostgreSQL的大小写敏感问题
- 符合PostgreSQL的命名约定
- 无需使用双引号包围字段名
- 更好的可读性和维护性

## 新增功能

### 1. 外键约束（可选）

在 PostgreSQL 版本中，我们添加了外键约束的选项：

```sql
-- 添加外键约束（可选）
-- ALTER TABLE app ADD CONSTRAINT fk_app_userId FOREIGN KEY (userId) REFERENCES "user"(id);
-- ALTER TABLE chat_history ADD CONSTRAINT fk_chat_history_appId FOREIGN KEY (appId) REFERENCES app(id);
-- ALTER TABLE chat_history ADD CONSTRAINT fk_chat_history_userId FOREIGN KEY (userId) REFERENCES "user"(id);
```

**优势:**
- 保证数据完整性
- 防止无效的外键引用
- 提供更好的数据约束

## 后续操作步骤

### 1. 环境准备

#### 安装 PostgreSQL
```bash
# Windows (使用 Chocolatey)
choco install postgresql

# 或下载官方安装包
# https://www.postgresql.org/download/windows/
```

#### 启动 PostgreSQL 服务
```bash
# Windows
net start postgresql-x64-14  # 版本号可能不同
```

### 2. 数据库初始化

#### 创建数据库和表
```bash
# 连接到 PostgreSQL
psql -U postgres

# 执行建表脚本
\i /path/to/create_table_postgresql.sql
```

#### 或者使用 pgAdmin
1. 打开 pgAdmin
2. 连接到 PostgreSQL 服务器
3. 创建新数据库 `ai_zcode`
4. 在查询工具中执行 `create_table_postgresql.sql`

### 3. 应用程序配置更新

#### 更新 application.yml
```yaml
spring:
  datasource:
    driver-class-name: org.postgresql.Driver
    url: jdbc:postgresql://localhost:5432/ai_zcode
    username: postgres
    password: your_password
```

#### 更新 pom.xml 依赖
```xml
<!-- 移除 MySQL 驱动 -->
<!-- <dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
    <scope>runtime</scope>
</dependency> -->

<!-- 添加 PostgreSQL 驱动 -->
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>
```

### 4. MyBatis-Flex 配置调整

#### 检查 SQL 语法兼容性
- 检查现有的 Mapper XML 文件
- 确保 SQL 语句与 PostgreSQL 兼容
- 特别注意分页查询语法差异

#### 可能需要调整的 SQL 语法
```sql
-- MySQL 分页
SELECT * FROM user LIMIT 10 OFFSET 20;

-- PostgreSQL 分页（相同语法，无需修改）
SELECT * FROM user LIMIT 10 OFFSET 20;

-- MySQL 字符串连接
CONCAT(field1, field2)

-- PostgreSQL 字符串连接
field1 || field2
```

### 5. 数据迁移（如果有现有数据）

#### 使用 pg_dump 和 mysqldump
```bash
# 从 MySQL 导出数据
mysqldump -u root -p ai_zcode > mysql_data.sql

# 转换并导入到 PostgreSQL（需要手动调整语法）
# 或使用迁移工具如 pgloader
```

#### 使用 pgloader（推荐）
```bash
# 安装 pgloader
# 创建迁移配置文件
pgloader mysql://user:password@localhost/ai_zcode postgresql://user:password@localhost/ai_zcode
```

### 6. 测试验证

#### 功能测试清单
- [ ] 数据库连接正常
- [ ] 用户注册/登录功能
- [ ] 应用创建/编辑功能
- [ ] 对话历史记录功能
- [ ] 自动更新时间戳功能
- [ ] 索引性能测试
- [ ] 外键约束测试（如果启用）

#### 性能测试
```sql
-- 测试索引效果
EXPLAIN ANALYZE SELECT * FROM "user" WHERE userAccount = 'test';
EXPLAIN ANALYZE SELECT * FROM app WHERE userId = 1;
EXPLAIN ANALYZE SELECT * FROM chat_history WHERE appId = 1 ORDER BY createTime DESC;
```

### 7. 监控和优化

#### PostgreSQL 特有的优化
```sql
-- 更新表统计信息
ANALYZE "user";
ANALYZE app;
ANALYZE chat_history;

-- 检查索引使用情况
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes;
```

## 注意事项

### 1. 数据类型差异
- PostgreSQL 对数据类型更严格
- 需要注意隐式类型转换的差异

### 2. 事务处理
- PostgreSQL 的事务隔离级别可能与 MySQL 不同
- 需要测试并发场景下的行为

### 3. 性能差异
- PostgreSQL 和 MySQL 的查询优化器不同
- 可能需要调整索引策略

### 4. 备份策略
- 使用 `pg_dump` 进行逻辑备份
- 考虑使用 `pg_basebackup` 进行物理备份

### 5. 字段名大小写敏感性 ⚠️ **关键问题** (已解决)
- **问题描述**: PostgreSQL 默认将所有未加引号的标识符转换为小写
- **常见错误**: `字段 "messageType" 不存在，建议：也许您想要引用列"chat_history.messagetype"`
- **最终解决方案**: 
  - ✅ **采用下划线命名约定**: 将所有驼峰字段改为下划线命名（如 `messageType` → `message_type`）
  - ✅ **更新Java实体类**: 修改 `@Column` 注解映射到新的字段名
  - ✅ **重新生成建表脚本**: 使用下划线命名的PostgreSQL脚本
- **影响范围**: 所有驼峰命名的字段、表名、索引名等
- **状态**: ✅ 已完成修复

## 总结

通过以上转换，我们成功将 MySQL 建表语句转换为 PostgreSQL 兼容的版本。主要改进包括：

1. **更严格的数据类型**: 使用 PostgreSQL 原生类型
2. **更好的约束支持**: 添加了外键约束选项
3. **触发器实现**: 使用触发器替代 MySQL 的 ON UPDATE 功能
4. **标准化语法**: 使用更标准的 SQL 语法

迁移完成后，应用程序将获得 PostgreSQL 的优势，包括更好的并发性能、更丰富的数据类型支持和更强的 ACID 特性。