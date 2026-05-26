# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作提供指导。

## 项目概览

这是一个 FastAPI + SQLAlchemy 后端开发学习项目。项目目前处于初始状态，结构非常简单。

## 技术栈

- **Web 框架**: FastAPI 0.136.1
- **ORM**: SQLAlchemy 2.0.30
- **数据序列化**: Pydantic 2.11.10
- **ASGI 服务器**: Uvicorn 0.44.0
- **设置管理**: Pydantic Settings

## 常用命令

```bash
# 运行开发服务器（自动重载）
uvicorn main:app --reload

# 指定主机和端口运行
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 类型检查
mypy .

# 代码检查
ruff .
```

## 项目结构（初始）

```
E:/Python/FASTAPI_SQL/
├── .claude/
│   └── settings.local.json
└── Todo list.py          # 空文件，准备用于开发
```

## 开发方式

1. 从简单的 FastAPI 应用程序结构开始
2. 逐步添加 SQLAlchemy 模型和数据库连接
3. 使用 Pydantic 模式实现 CRUD 操作
4. 逐步添加认证、验证和高级功能

## 核心学习路径

1. **FastAPI 基础**: 路由、请求/响应模型、查询/主体参数
2. **SQLAlchemy 数据库**: 模型定义、会话管理、CRUD 操作
3. **Pydantic**: 数据验证、模式定义
4. **进阶主题**: 认证、依赖注入、测试、数据库迁移

## MySQL 配置文件修改（my.cnf / my.ini）

以下配置需要修改 MySQL 配置文件，无法通过 SQL 语句实现：

### 1. 主从复制 (Master-Slave Replication)
```ini
# 主服务器配置
[mysqld]
server-id=1
log-bin=mysql-bin
binlog-format=row

# 从服务器配置
[mysqld]
server-id=2
relay-log=relay-log
log-bin=mysql-bin
```

### 2. 二进制日志 (Binlog)
```ini
[mysqld]
log-bin=mysql-bin
binlog-format=row
expire-logs-days=7
```

### 3. 慢查询日志
```ini
[mysqld]
slow-query-log=1
slow-query-log-file=/var/log/mysql/slow.log
long-query-time=2
```

### 4. 重做日志 (Redo Log) 和 撤销日志 (Undo Log)
```ini
[mysqld]
innodb-log-file-size=256M
innodb-log-buffer-size=16M
innodb-undo-log-truncate=on
```

### 5. 其他高级配置
```ini
[mysqld]
innodb-buffer-pool-size=1G
innodb-lock-wait-timeout=120
innodb-flush-log-at-trx-commit=1
```

### 修改步骤
1. 找到 MySQL 配置文件位置：`mysql --verbose --help | grep my.cnf`
2. 编辑 `my.cnf` (Linux) 或 `my.ini` (Windows)
3. 重启 MySQL 服务：`sudo service mysql restart`

## SQL 语言基础

### 一、SQL 分类

| 类型 | 全称 | 说明 | 示例 |
|------|------|------|------|
| **DDL** | Data Definition Language | 数据定义语言（建表、改表结构） | CREATE, ALTER, DROP |
| **DML** | Data Manipulation Language | 数据操作语言（增删改查） | INSERT, UPDATE, DELETE, SELECT |
| **DCL** | Data Control Language | 数据控制语言（权限管理） | GRANT, REVOKE |
| **TCL** | Transaction Control Language | 事务控制语言 | COMMIT, ROLLBACK |

### 二、CREATE TABLE 完整语法

```sql
CREATE TABLE [IF NOT EXISTS] 表名 (
    -- 1. 列定义：列名 数据类型 [约束] [默认值] [注释]
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    age INT DEFAULT 0 COMMENT '年龄',
    
    -- 2. 主键定义（ alternatives to PRIMARY KEY in column definition）
    PRIMARY KEY (id),
    
    -- 3. 外键定义
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- 4. 唯一约束
    UNIQUE KEY uk_email (email),
    
    -- 5. 索引定义（加速查询）
    INDEX idx_username (username),
    INDEX idx_status_created (status, created_at),  -- 复合索引
    
    -- 6. 全文索引（文本搜索）
    FULLTEXT KEY ft_content (content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表注释';
```

### 三、约束条件（Constraints）

| 约束 | 说明 |
|------|------|
| `PRIMARY KEY` | 主键（唯一标识每一行） |
| `FOREIGN KEY` | 外键（关联其他表） |
| `UNIQUE` | 唯一约束（不能重复） |
| `NOT NULL` | 非空约束 |
| `DEFAULT` | 默认值 |
| `CHECK` | 检查约束（如：CHECK (age >= 0)） |

### 四、索引（Indexes）

| 索引类型 | 语法 | 用途 |
|----------|------|------|
| 主键索引 | `PRIMARY KEY (id)` | 自动创建，唯一 |
| 唯一索引 | `UNIQUE KEY uk_name (col)` | 保证唯一性 |
| 普通索引 | `INDEX idx_name (col)` | 加速查询 |
| 复合索引 | `INDEX idx_a_b (a, b)` | 多列联合查询 |
| 全文索引 | `FULLTEXT KEY ft_name (content)` | 文本搜索 |

**为什么需要索引？**
- 没有索引：数据库需要全表扫描（慢）
- 有索引：数据库直接定位到数据（快）

**复合索引最左前缀原则：**
```sql
INDEX idx_a_b_c (a, b, c)
-- 以下查询会使用索引：
WHERE a = 1
WHERE a = 1 AND b = 2
WHERE a = 1 AND b = 2 AND c = 3
-- 以下查询不会使用索引：
WHERE b = 2
WHERE c = 3
```

### 五、存储引擎

| 引擎 | 事务 | 行锁 | 外键 | 适用场景 |
|------|------|------|------|----------|
| **InnoDB** | ✅ | ✅ | ✅ | 一般业务（支持事务、行锁） |
| MyISAM | ❌ | ❌ | ❌ | 读多写少（性能高） |

### 六、常用数据类型

| 类型 | 说明 |
|------|------|
| `INT` | 整数 |
| `VARCHAR(n)` | 变长字符串 |
| `TEXT` | 长文本 |
| `DECIMAL(m,d)` | 精确小数（如价格） |
| `TIMESTAMP` | 时间戳 |
| `ENUM` | 枚举类型 |
| `JSON` | JSON 格式数据 |

### 七、事务（Transaction）

```sql
-- 开启事务
START TRANSACTION;

-- 执行 SQL
INSERT INTO users (name) VALUES ('张三');
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;

-- 提交事务（保存更改）
COMMIT;

-- 或回滚事务（撤销更改）
ROLLBACK;
```

**事务四大特性（ACID）：**
- **原子性**：要么全部成功，要么全部失败
- **一致性**：数据状态保持一致
- **隔离性**：并发事务互不干扰
- **持久性**：提交后永久保存

### 八、SQL 执行顺序

```sql
SELECT           -- 7. 返回结果
DISTINCT         -- 8. 去重
FROM             -- 1. 从哪张表
JOIN             -- 2. 关联表
ON               -- 3. 连接条件
WHERE            -- 4. 行筛选
GROUP BY         -- 5. 分组
HAVING           -- 6. 分组后筛选
ORDER BY         -- 9. 排序
LIMIT            -- 10. 限制数量
```

## 当前任务：旅游收藏夹 API（2026-05-26）

### 项目目标
使用 **pymysql + 原生 SQL** 实现一个完整的旅游景点收藏系统，学习 FastAPI 后端开发和 SQL 核心知识。

### 技术栈（更新）

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI 0.136.1 | Python 异步 Web 框架 |
| 数据库 | MySQL | 关系型数据库 |
| 数据库驱动 | pymysql 1.1.0 | 原生 MySQL 连接，学习 SQL 核心 |
| 数据验证 | Pydantic 2.11.10 | 数据序列化/反序列化 |
| ASGI 服务器 | Uvicorn 0.44.0 | Python ASGI 服务器 |

### 项目结构（当前）

```
E:/Python/FASTAPI_SQL/
├── .claude/
│   └── settings.local.json
├── main.py              # FastAPI 应用入口（路由定义）
├── database.py          # 数据库连接管理（pymysql）
├── model.py             # SQL 表结构定义（DDL）
├── crud.py              # 数据库 CRUD 操作（DML）
├── schemas.py           # Pydantic 模式定义
├── utils.py             # 工具函数（CSV 导入、密码加密等）
├── data/                # CSV 数据目录
│   └── attraction_data/
└── full-stack-fastapi-template/  # 参考的全栈模板项目
```

### 数据库设计

#### 1. users 表（用户表）
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 2. attractions 表（景点表）
```sql
CREATE TABLE attractions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    attraction_id INT UNIQUE NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    attraction_name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    longitude DECIMAL(10, 6),
    latitude DECIMAL(10, 6),
    open_hours VARCHAR(100),
    ticket_price DECIMAL(10, 2),
    overview TEXT,
    facilities TEXT,
    type VARCHAR(100),
    duration_of_visit VARCHAR(50),
    rate_of_restaurant DECIMAL(3, 2),
    facilities_group TEXT,
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_city (city_name),
    INDEX idx_type (type),
    INDEX idx_city_type (city_name, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### 3. bookmarks 表（收藏表）
```sql
CREATE TABLE bookmarks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    attraction_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_attraction (user_id, attraction_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (attraction_id) REFERENCES attractions(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_attraction (attraction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### API 接口设计

| 接口 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 欢迎页 |
| `/api/attractions` | GET | 获取景点列表（分页、搜索、筛选） |
| `/api/attractions/{id}` | GET | 获取景点详情 |
| `/api/attractions/city/{city}` | GET | 按城市筛选 |
| `/api/attractions/type/{type}` | GET | 按类型筛选 |
| `/api/bookmarks` | GET | 我的收藏列表 |
| `/api/bookmarks/{id}` | POST | 收藏景点 |
| `/api/bookmarks/{id}` | DELETE | 取消收藏 |
| `/api/register` | POST | 用户注册 |
| `/api/login` | POST | 用户登录 |
| `/api/me` | GET | 获取当前用户信息 |

### 已完成工作

| 任务 | 状态 | 说明 |
|------|------|------|
| 创建 User 表 | ✅ | users 表定义在 model.py |
| 创建 Attraction 表 | ✅ | attractions 表定义在 model.py |
| 创建 Bookmark 表 | ✅ | bookmarks 表定义在 model.py |
| 修改 database.py | ✅ | 自动创建数据库和表 |
| 修改 main.py | ✅ | 定义 API 路由框架 |

### 待完成任务

| 任务 | 状态 | 说明 |
|------|------|------|
| CRUD 操作 | ⏳ | 编写 crud.py 实现增删改查 |
| CSV 导入脚本 | ⏳ | 将 attraction_data CSV 导入数据库 |
| API 实现 | ⏳ | 完善 main.py 中的路由逻辑 |
| 数据验证 | ⏳ | 使用 Pydantic 定义请求/响应模型 |
| 认证系统 | ⏳ | JWT 用户认证 |

### ETL 流程（数据导入）

1. **Extract**: 从 CSV 文件读取数据
2. **Transform**: 数据清洗、类型转换、JSON 解析
3. **Load**: 插入数据库

### 设计决策记录

1. **为什么用 pymysql 而不是 SQLAlchemy ORM？**
   - 学习 SQL 核心知识（DDL/DML/DQL）
   - 理解数据库底层操作
   - 更灵活的查询控制

2. **为什么有 `id` 和 `attraction_id` 两个主键？**
   - `id`: 数据库自增主键（内部使用）
   - `attraction_id`: 原始 CSV 数据的 ID（业务使用）

3. **外键级联删除 (`ON DELETE CASCADE`)**
   - 删除用户时自动删除其收藏
   - 删除景点时自动删除相关收藏记录
