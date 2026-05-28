"""
database.py - SQLite 数据库连接管理
用于演示项目，无需安装 MySQL
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# 导入表结构定义（从 model.py 复制过来）
CREATE_USER_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT 1,
    is_superuser BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_ATTRACTION_TABLE = """
CREATE TABLE IF NOT EXISTS attractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attraction_id INTEGER NOT NULL,
    source_type VARCHAR(20) DEFAULT 'domestic',
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_BOOKMARK_TABLE = """
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    attraction_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, attraction_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (attraction_id) REFERENCES attractions(id) ON DELETE CASCADE
)
"""

CREATE_TRANSPORT_TABLE = """
CREATE TABLE IF NOT EXISTS transport_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id VARCHAR(50) NOT NULL,
    transport_type VARCHAR(20) NOT NULL,
    from_location VARCHAR(100) NOT NULL,
    to_location VARCHAR(100) NOT NULL,
    begin_time VARCHAR(10),
    end_time VARCHAR(10),
    duration DECIMAL(5, 2),
    cost DECIMAL(10, 2)
)
"""


def init_db():
    """初始化数据库，创建所有表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(CREATE_USER_TABLE)
    cursor.execute(CREATE_ATTRACTION_TABLE)
    cursor.execute(CREATE_BOOKMARK_TABLE)
    cursor.execute(CREATE_TRANSPORT_TABLE)

    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")


def get_db():
    """数据库连接生成器 (FastAPI 依赖注入兼容)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def get_conn():
    """直接获取数据库连接 (用于脚本)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# 测试
if __name__ == "__main__":
    init_db()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM attractions")
    print(f"景点数量: {cursor.fetchone()['count']}")
    cursor.close()
    conn.close()
