"""
ETL 数据导入脚本
统一将 knowledge/ 下的 5 类数据源清洗、转换并写入 MySQL
"""
import csv
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_mysql_connection

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE = os.path.join(BASE, "knowledge")
DESTINATIONS = os.path.join(KNOWLEDGE, "destinations", "database")
GLOBAL_DATA = os.path.join(KNOWLEDGE, "datas", "attraction_data")

# 国内 10 城列表
DOMESTIC_CITIES = [
    "beijing", "shanghai", "guangzhou", "shenzhen", "hangzhou",
    "chengdu", "nanjing", "wuhan", "suzhou", "chongqing"
]

# 英文城市名 → 中文城市名映射
CITY_MAP = {
    "Beijing": "北京", "Shanghai": "上海", "Guangzhou": "广州",
    "Shenzhen": "深圳", "Hangzhou": "杭州", "Chengdu": "成都",
    "Nanjing": "南京", "Wuhan": "武汉", "Suzhou": "苏州",
    "Chongqing": "重庆", "Changsha": "长沙", "Changchun": "长春",
    "Tokyo": "东京", "Osaka": "大阪", "Seoul": "首尔", "Busan": "釜山",
    "Bangkok": "曼谷", "Singapore": "新加坡", "Kuala Lumpur": "吉隆坡",
    "Hong Kong": "香港", "Macau": "澳门", "Taipei": "台北",
    "Jakarta": "雅加达", "Bali": "巴厘岛", "Manila": "马尼拉",
    "Hanoi": "河内", "Ho Chi Minh City": "胡志明市", "Phnom Penh": "金边",
    "Yangon": "仰光", "Dubai": "迪拜", "Abu Dhabi": "阿布扎比",
    "Abu": "阿布扎比", "Doha": "多哈", "Riyadh": "利雅得", "Muscat": "马斯喀特",
    "Istanbul": "伊斯坦布尔", "Ankara": "安卡拉", "Antalya": "安塔利亚",
    "Moscow": "莫斯科", "Saint Petersburg": "圣彼得堡",
    "London": "伦敦", "Paris": "巴黎", "Berlin": "柏林",
    "Rome": "罗马", "Milan": "米兰", "Venice": "威尼斯",
    "Madrid": "马德里", "Barcelona": "巴塞罗那", "Lisbon": "里斯本",
    "Amsterdam": "阿姆斯特丹", "Brussels": "布鲁塞尔",
    "Vienna": "维也纳", "Prague": "布拉格", "Budapest": "布达佩斯",
    "Warsaw": "华沙", "Athens": "雅典", "Zurich": "苏黎世",
    "Geneva": "日内瓦", "Stockholm": "斯德哥尔摩", "Oslo": "奥斯陆",
    "Copenhagen": "哥本哈根", "Helsinki": "赫尔辛基", "Dublin": "都柏林",
    "New York": "纽约", "Los Angeles": "洛杉矶", "San Francisco": "旧金山",
    "Chicago": "芝加哥", "Boston": "波士顿", "Washington": "华盛顿",
    "Seattle": "西雅图", "Miami": "迈阿密", "Las Vegas": "拉斯维加斯",
    "Toronto": "多伦多", "Vancouver": "温哥华", "Montreal": "蒙特利尔",
    "Sydney": "悉尼", "Melbourne": "墨尔本", "Brisbane": "布里斯班",
    "Auckland": "奥克兰", "Wellington": "惠灵顿",
    "Cairo": "开罗", "Cape Town": "开普敦", "Nairobi": "内罗毕",
    "Casablanca": "卡萨布兰卡", "Marrakech": "马拉喀什",
    "Mexico City": "墨西哥城", "Cancún": "坎昆", "Havana": "哈瓦那",
    "Rio de Janeiro": "里约热内卢", "São Paulo": "圣保罗",
    "Buenos Aires": "布宜诺斯艾利斯", "Lima": "利马", "Santiago": "圣地亚哥",
    "Bogota": "波哥大", "Bogotá": "波哥大",
}

# ==========================================
# 数据源 1：国内景点 CSV（10 城）
# ==========================================
def import_attractions_domestic(conn):
    """读取 destinations/database/attractions/{city}/attractions.csv"""
    total = 0
    cursor = conn.cursor()

    for city_en in DOMESTIC_CITIES:
        city_cn = CITY_MAP.get(city_en.capitalize(), city_en)
        filepath = os.path.join(DESTINATIONS, "attractions", city_en, "attractions.csv")
        if not os.path.exists(filepath):
            print(f"  [跳过] 文件不存在: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                attraction_id = int(row["id"])
                name = row["name"].strip()
                att_type = row.get("type", "")
                lat = float(row["lat"]) if row.get("lat") else None
                lon = float(row["lon"]) if row.get("lon") else None
                opentime = row.get("opentime", "")
                endtime = row.get("endtime", "")
                open_hours = f"{opentime}-{endtime}" if opentime and endtime else ""
                price = float(row["price"]) if row.get("price") else 0.0
                mintime = row.get("recommendmintime", "")
                maxtime = row.get("recommendmaxtime", "")
                duration = f"{mintime}-{maxtime}小时" if mintime and maxtime else ""

                sql = """
                    INSERT INTO attractions
                        (attraction_id, source_type, city_name, attraction_name, type,
                         latitude, longitude, open_hours, ticket_price, duration_of_visit)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE attraction_name=VALUES(attraction_name)
                """
                cursor.execute(sql, (
                    attraction_id, "domestic", city_cn, name, att_type,
                    lat, lon, open_hours, price, duration
                ))
                total += 1

    conn.commit()
    cursor.close()
    print(f"  [国内景点] 导入 {total} 条")


# ==========================================
# 数据源 4：全球景点 CSV（knowledge/datas/attraction_data/）
# ==========================================
def import_attractions_foreign(conn):
    """读取 datas/attraction_data/*_attraction.csv"""
    total = 0
    cursor = conn.cursor()

    for filename in os.listdir(GLOBAL_DATA):
        if not filename.endswith("_attraction.csv"):
            continue
        filepath = os.path.join(GLOBAL_DATA, filename)
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                attraction_id = int(row["attraction_id"])
                city_en = row.get("city_name", "").strip()
                city_cn = CITY_MAP.get(city_en, city_en)
                name = row.get("attraction_name", "").strip()
                att_type = row.get("type", "").strip()
                lat = float(row["latitude"]) if row.get("latitude") else None
                lon = float(row["longitude"]) if row.get("longitude") else None
                open_hours = row.get("open_hours", "").strip()
                price = float(row["ticket_price"]) if row.get("ticket_price") else 0.0
                duration = row.get("duration_of_visit", "").strip()
                overview = row.get("overview", "").strip()
                country = row.get("country", "").strip()
                address = row.get("address", "").strip()
                facilities = row.get("facilities", "").strip()
                facilities_group = row.get("facilities_group", "").strip()
                rate = float(row["rate_of_restaurant"]) if row.get("rate_of_restaurant") else None

                try:
                    sql = """
                        INSERT INTO attractions
                            (attraction_id, source_type, city_name, attraction_name, type,
                             latitude, longitude, open_hours, ticket_price, duration_of_visit,
                             overview, country, address, facilities, rate_of_restaurant,
                             facilities_group)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE attraction_name=VALUES(attraction_name)
                    """
                    cursor.execute(sql, (
                        attraction_id, "foreign", city_cn, name, att_type,
                        lat, lon, open_hours, price, duration,
                        overview, country, address, facilities, rate,
                        facilities_group
                    ))
                    total += 1
                except Exception as e:
                    print(f"  [警告] 插入失败 attraction_id={attraction_id}: {e}")

    conn.commit()
    cursor.close()
    print(f"  [全球景点] 导入 {total} 条")


# ==========================================
# 数据源 2：酒店 CSV（10 城）
# ==========================================
def import_accommodations(conn):
    """读取 destinations/database/accommodations/{city}/accommodations.csv"""
    total = 0
    cursor = conn.cursor()

    for city_en in DOMESTIC_CITIES:
        city_cn = CITY_MAP.get(city_en.capitalize(), city_en)
        filepath = os.path.join(DESTINATIONS, "accommodations", city_en, "accommodations.csv")
        if not os.path.exists(filepath):
            print(f"  [跳过] 文件不存在: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                acc_id = int(row["id"])
                name = row["name"].strip()
                name_en = row.get("hotelname_en", "").strip()
                feature = row.get("featurehoteltype", "").strip()
                lat = float(row["lat"]) if row.get("lat") else None
                lon = float(row["lon"]) if row.get("lon") else None
                price = float(row["price"]) if row.get("price") else 0.0
                numbed = int(row["numbed"]) if row.get("numbed") else 1

                sql = """
                    INSERT INTO accommodations
                        (accommodation_id, city_name, name, name_en, feature_type,
                         latitude, longitude, ticket_price, num_bed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name)
                """
                cursor.execute(sql, (
                    acc_id, city_cn, name, name_en, feature,
                    lat, lon, price, numbed
                ))
                total += 1

    conn.commit()
    cursor.close()
    print(f"  [酒店] 导入 {total} 条")


# ==========================================
# 数据源 3：餐厅 CSV（10 城）
# ==========================================
def import_restaurants(conn):
    """读取 destinations/database/restaurants/{city}/restaurants_{city}.csv"""
    total = 0
    cursor = conn.cursor()

    for city_en in DOMESTIC_CITIES:
        city_cn = CITY_MAP.get(city_en.capitalize(), city_en)
        filename = f"restaurants_{city_en}.csv"
        filepath = os.path.join(DESTINATIONS, "restaurants", city_en, filename)
        if not os.path.exists(filepath):
            print(f"  [跳过] 文件不存在: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rest_id = int(row["id"])
                name = row["name"].strip()
                lat = float(row["lat"]) if row.get("lat") else None
                lon = float(row["lon"]) if row.get("lon") else None
                price = float(row["price"]) if row.get("price") else 0.0
                cuisine = row.get("cuisine", "").strip()
                opentime = row.get("opentime", "")
                endtime = row.get("endtime", "")
                open_hours = f"{opentime}-{endtime}" if opentime and endtime else ""
                foods = row.get("recommendedfood", "").strip()

                sql = """
                    INSERT INTO restaurants
                        (restaurant_id, city_name, name, latitude, longitude,
                         ticket_price, cuisine, open_hours, recommended_foods)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE name=VALUES(name)
                """
                cursor.execute(sql, (
                    rest_id, city_cn, name, lat, lon,
                    price, cuisine, open_hours, foods
                ))
                total += 1

    conn.commit()
    cursor.close()
    print(f"  [餐厅] 导入 {total} 条")


# ==========================================
# 数据源 5：交通路线（飞机 JSONL + 火车 JSON）
# ==========================================
def import_transport(conn):
    total = 0
    cursor = conn.cursor()

    # 5a. 飞机航班（JSONL）
    airplane_path = os.path.join(DESTINATIONS, "intercity_transport", "airplane.jsonl")
    if os.path.exists(airplane_path):
        with open(airplane_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                route_id = obj["FlightID"]
                from_loc = obj.get("From", "")
                to_loc = obj.get("To", "")
                begin = obj.get("BeginTime", "")
                end = obj.get("EndTime", "")
                duration = float(obj["Duration"]) if obj.get("Duration") else 0
                cost = float(obj["Cost"]) if obj.get("Cost") else 0

                sql = """
                    INSERT INTO transport_routes
                        (route_id, transport_type, from_location, to_location,
                         begin_time, end_time, duration, cost)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE cost=VALUES(cost)
                """
                cursor.execute(sql, (
                    route_id, "airplane", from_loc, to_loc,
                    begin, end, duration, cost
                ))
                total += 1
    else:
        print(f"  [跳过] 文件不存在: {airplane_path}")

    # 5b. 火车班次（JSON 数组）
    train_dir = os.path.join(DESTINATIONS, "intercity_transport", "train")
    if os.path.exists(train_dir):
        for filename in os.listdir(train_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(train_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                train_list = json.load(f)
                for obj in train_list:
                    # 构建唯一 route_id
                    route_id = f"{obj['TrainID']}_{filename.replace('.json','')}"
                    from_loc = obj.get("From", "")
                    to_loc = obj.get("To", "")
                    t_type_cn = obj.get("TrainType", "")

                    # 火车类型英文映射
                    type_map = {"高铁": "high_speed", "动车": "bullet",
                                "特快": "express", "快速": "fast",
                                "直达特快": "direct_express"}
                    transport_type = type_map.get(t_type_cn, "train")

                    begin = obj.get("BeginTime", "")
                    end = obj.get("EndTime", "")
                    duration = float(obj["Duration"]) if obj.get("Duration") else 0
                    cost = float(obj["Cost"]) if obj.get("Cost") else 0

                    try:
                        sql = """
                            INSERT INTO transport_routes
                                (route_id, transport_type, from_location, to_location,
                                 begin_time, end_time, duration, cost)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE cost=VALUES(cost)
                        """
                        cursor.execute(sql, (
                            route_id, transport_type, from_loc, to_loc,
                            begin, end, duration, cost
                        ))
                        total += 1
                    except Exception as e:
                        print(f"  [警告] 火车插入失败 {route_id}: {e}")

    conn.commit()
    cursor.close()
    print(f"  [交通路线] 导入 {total} 条")


# ==========================================
# 主入口
# ==========================================
def main():
    print("=" * 60)
    print("ETL 数据导入脚本")
    print("=" * 60)

    conn = get_mysql_connection()
    try:
        print("\n[1/5] 导入国内景点...")
        import_attractions_domestic(conn)

        print("\n[2/5] 导入全球景点...")
        import_attractions_foreign(conn)

        print("\n[3/5] 导入酒店数据...")
        import_accommodations(conn)

        print("\n[4/5] 导入餐厅数据...")
        import_restaurants(conn)

        print("\n[5/5] 导入交通路线...")
        import_transport(conn)

        print("\n" + "=" * 60)
        print("全部导入完成！")
        print("=" * 60)

        # 统计信息
        cursor = conn.cursor()
        for table in ["attractions", "accommodations", "restaurants", "transport_routes"]:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            cnt = cursor.fetchone()["cnt"]
            print(f"  {table}: {cnt} 条记录")
        cursor.close()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
