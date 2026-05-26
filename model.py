# ==========================================
# User 表 - 用于用户注册和登录
# ==========================================
CREATE_USER_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱（登录账号）',
    hashed_password VARCHAR(255) NOT NULL COMMENT '加密后的密码',
    full_name VARCHAR(255) COMMENT '全名',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_superuser BOOLEAN DEFAULT FALSE COMMENT '是否超级管理员',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
"""

# ==========================================
# Attraction 表 - 景点数据（从 CSV 导入）
# ==========================================
CREATE_ATTRACTION_TABLE = """
CREATE TABLE IF NOT EXISTS attractions (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '内部主键',
    attraction_id INT UNIQUE NOT NULL COMMENT '原始景点ID',
    city_name VARCHAR(100) NOT NULL COMMENT '城市名称',
    attraction_name VARCHAR(200) NOT NULL COMMENT '景点名称',
    address VARCHAR(500) COMMENT '地址',
    longitude DECIMAL(10, 6) COMMENT '经度',
    latitude DECIMAL(10, 6) COMMENT '纬度',
    open_hours VARCHAR(100) COMMENT '开放时间',
    ticket_price DECIMAL(10, 2) COMMENT '门票价格',
    overview TEXT COMMENT '概述',
    facilities TEXT COMMENT '设施（JSON）',
    type VARCHAR(100) COMMENT '类型',
    duration_of_visit VARCHAR(50) COMMENT '建议游览时间',
    rate_of_restaurant DECIMAL(3, 2) COMMENT '餐厅评分',
    facilities_group TEXT COMMENT '设施分组（JSON）',
    country VARCHAR(50) COMMENT '国家',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_city (city_name),
    INDEX idx_type (type),
    INDEX idx_city_type (city_name, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='景点表';
"""

# ==========================================
# Bookmark 表 - 用户收藏夹
# ==========================================
CREATE_BOOKMARK_TABLE = """
CREATE TABLE IF NOT EXISTS bookmarks (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键',
    user_id INT NOT NULL COMMENT '用户ID',
    attraction_id INT NOT NULL COMMENT '景点ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    UNIQUE KEY uk_user_attraction (user_id, attraction_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (attraction_id) REFERENCES attractions(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_attraction (attraction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户收藏表';
"""