from contextlib import contextmanager
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql

# 导入表结构定义
from model import (
    CREATE_USER_TABLE,
    CREATE_ATTRACTION_TABLE,
    CREATE_BOOKMARK_TABLE
)

def get_mysql_connection():
    """获取 MySQL 连接（自动创建数据库和表，类似 SQLite 的自动创建行为）"""
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "2241829725")
    database = os.getenv("MYSQL_DATABASE", "agent_test0")

    # 先连接到 MySQL 服务器（不指定数据库）
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    # 自动创建数据库（如果不存在）
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    cursor.close()

    # 再连接到指定数据库
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    # 自动创建表（如果不存在）
    create_tables(conn)

    return conn

def create_tables(conn):
    """创建所有必要的表"""
    cursor = conn.cursor()

    # 创建 User 表
    cursor.execute(CREATE_USER_TABLE)

    # 创建 Attraction 表
    cursor.execute(CREATE_ATTRACTION_TABLE)

    # 创建 Bookmark 表
    cursor.execute(CREATE_BOOKMARK_TABLE)

    conn.commit()
    cursor.close()

@contextmanager
def get_db():
    """数据库上下文管理器，自动管理连接"""
    conn = get_mysql_connection()
    try:
        yield conn
    finally:
        conn.close()  # 自动关闭连接

# 测试代码：查询 attractions 表
if __name__ == "__main__":
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attractions LIMIT 5")
        result = cursor.fetchall()
        print("Attractions data:", result)
