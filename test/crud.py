"""
crud.py - SQLite 数据库 CRUD 操作
注意：使用 ? 占位符而非 %s
"""
from typing import Optional, List, Dict, Any


def get_attraction_by_id(db, attraction_id: int) -> Optional[Dict[str, Any]]:
    """根据原始 attraction_id 获取单个景点详情"""
    cursor = db.cursor()
    sql = "SELECT * FROM attractions WHERE id = ?"
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
        base_sql += " AND city_name = ?"
        params_list.append(city)
    if attraction_type:
        base_sql += " AND type = ?"
        params_list.append(attraction_type)
    if search:
        base_sql += " AND (attraction_name LIKE ? OR city_name LIKE ?)"
        search_term = f"%{search}%"
        params_list.extend([search_term, search_term])

    # 2. 查询分页数据
    data_sql = f"SELECT * {base_sql} ORDER BY id DESC LIMIT ? OFFSET ?"
    query_params = params_list + [limit, skip]
    cursor.execute(data_sql, query_params)
    results = cursor.fetchall()

    # 3. 动态查询总数
    count_sql = f"SELECT COUNT(*) as count {base_sql}"
    cursor.execute(count_sql, params_list)
    count_res = cursor.fetchone()
    count = count_res["count"] if count_res else 0

    cursor.close()
    return results, count


def check_user_exists_by_email(db, email: str) -> bool:
    """检查邮箱是否已被注册"""
    cursor = db.cursor()
    sql = "SELECT id FROM users WHERE email = ?"
    cursor.execute(sql, (email,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def create_user(db, email: str, hashed_password: str, full_name: Optional[str] = None) -> int:
    """创建新用户，返回生成的用户 ID"""
    cursor = db.cursor()
    sql = "INSERT INTO users (email, hashed_password, full_name) VALUES (?, ?, ?)"
    cursor.execute(sql, (email, hashed_password, full_name))
    db.commit()
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


def get_user_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    """根据邮箱获取用户信息（登录校验用）"""
    cursor = db.cursor()
    sql = "SELECT * FROM users WHERE email = ?"
    cursor.execute(sql, (email,))
    user = cursor.fetchone()
    cursor.close()
    return user


def add_bookmark(db, user_id: int, attraction_id: int) -> bool:
    """添加收藏（利用 INSERT OR IGNORE 规避重复报错）"""
    cursor = db.cursor()
    sql = "INSERT OR IGNORE INTO bookmarks (user_id, attraction_id) VALUES (?, ?)"
    cursor.execute(sql, (user_id, attraction_id))
    db.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    return affected_rows > 0


def remove_bookmark(db, user_id: int, attraction_id: int) -> bool:
    """取消收藏"""
    cursor = db.cursor()
    sql = "DELETE FROM bookmarks WHERE user_id = ? AND attraction_id = ?"
    cursor.execute(sql, (user_id, attraction_id))
    db.commit()
    affected_rows = cursor.rowcount
    cursor.close()
    return affected_rows > 0


def get_user_bookmarks_with_details(db, user_id: int) -> List[Dict[str, Any]]:
    """获取用户收藏的景点详细信息"""
    cursor = db.cursor()
    sql = """
        SELECT
            b.id,
            b.attraction_id,
            b.created_at,
            a.attraction_name,
            a.city_name,
            a.ticket_price,
            a.type
        FROM bookmarks b
        INNER JOIN attractions a ON b.attraction_id = a.id
        WHERE b.user_id = ?
        ORDER BY b.id DESC
    """
    cursor.execute(sql, (user_id,))
    results = cursor.fetchall()
    cursor.close()
    return results


def get_transport_routes_by_city(db, city_name: str) -> List[Dict[str, Any]]:
    """根据城市名获取相关交通路线（最多返回10条）"""
    cursor = db.cursor()
    sql = """
        SELECT route_id, transport_type, from_location, to_location,
               begin_time, end_time, duration, cost
        FROM transport_routes
        WHERE from_location LIKE ? OR to_location LIKE ?
        ORDER BY begin_time
        LIMIT 10
    """
    search_term = f"%{city_name}%"
    cursor.execute(sql, (search_term, search_term))
    results = cursor.fetchall()
    cursor.close()
    return results
