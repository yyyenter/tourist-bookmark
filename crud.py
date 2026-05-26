"""
crud.py - 数据库增删改查核心逻辑
支持被 FastAPI 路由层和后台 Multi-Agent (如 crewAI) 共同调用
"""
from typing import Optional, List, Dict, Any
from pymysql.cursors import DictCursor

def get_attraction_by_id(db, attraction_id: int) -> Optional[Dict[str, Any]]:
    """根据原始 attraction_id 获取单个景点详情"""
    cursor = db.cursor()
    sql = "SELECT * FROM attractions WHERE attraction_id = %s"
    cursor.execute(sql, (attraction_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

def fetch_attractions(
    db, 
    limit: int = 10, 
    skip: int = 0, 
    city: Optional[str] = None, 
    attraction_type: Optional[str] = None, 
    search: Optional[str] = None
) -> tuple[List[Dict[str, Any]], int]:
    """
    通用景点检索（支持条件组合筛选、模糊搜索与标准分页）
    返回: (景点数据列表, 满足筛选条件的总记录数)
    """
    cursor = db.cursor()
    
    # 1. 动态构建查询数据 SQL
    base_sql = "FROM attractions WHERE 1=1"
    params_list = []

    if city:
        base_sql += " AND city_name = %s"
        params_list.append(city)
    if attraction_type:
        base_sql += " AND type = %s"
        params_list.append(attraction_type)
    if search:
        base_sql += " AND (attraction_name LIKE %s OR city_name LIKE %s)"
        search_term = f"%{search}%"
        params_list.extend([search_term, search_term])

    # 2. 查询分页数据
    data_sql = f"SELECT * {base_sql} ORDER BY id DESC LIMIT %s OFFSET %s"
    # 注意：Limit 和 Offset 的参数需要跟在条件参数后面
    query_params = params_list + [limit, skip]
    cursor.execute(data_sql, query_params)
    results = cursor.fetchall()

    # 3. 动态查询总数 (Count 逻辑保持与筛选条件严格一致)
    count_sql = f"SELECT COUNT(*) as count {base_sql}"
    cursor.execute(count_sql, params_list)
    count_res = cursor.fetchone()
    count = count_res["count"] if count_res else 0

    cursor.close()
    return results, count

def check_user_exists_by_email(db, email: str) -> bool:
    """检查邮箱是否已被注册"""
    cursor = db.cursor()
    sql = "SELECT id FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists

def create_user(db, email: str, hashed_password: str, full_name: Optional[str] = None) -> int:
    """创建新用户，返回生成的用户 ID"""
    cursor = db.cursor()
    sql = "INSERT INTO users (email, hashed_password, full_name) VALUES (%s, %s, %s)"
    cursor.execute(sql, (email, hashed_password, full_name))
    db.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id

def get_user_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    """根据邮箱获取用户信息（登录校验用）"""
    cursor = db.cursor()
    sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    user = cursor.fetchone()
    cursor.close()
    return user