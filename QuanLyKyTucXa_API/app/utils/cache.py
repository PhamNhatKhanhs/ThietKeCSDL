import redis
from flask import current_app, g
import json
import datetime

# Hàm helper để serialize các kiểu dữ liệu không chuẩn của JSON
def json_serializer(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_redis():
    """Khởi tạo hoặc trả về Redis client."""
    if 'redis' not in g:
        try:
            print("Connecting to Redis...")
            g.redis = redis.Redis(
                host=current_app.config['REDIS_HOST'],
                port=current_app.config['REDIS_PORT'],
                db=current_app.config['REDIS_DB'],
                decode_responses=True # Tự động decode bytes thành string
            )
            g.redis.ping() # Kiểm tra kết nối
            print("Redis connected successfully.")
        except redis.exceptions.ConnectionError as err:
            print(f"Lỗi kết nối Redis: {err}")
            g.redis = None # Đặt là None nếu không kết nối được
    return g.redis

def set_cache(key, value, ttl=None):
    """Lưu giá trị vào cache Redis."""
    redis_client = get_redis()
    if redis_client:
        try:
            # Chuyển đổi value thành JSON nếu nó là dict hoặc list
            if isinstance(value, (dict, list)):
                # Sử dụng json_serializer để xử lý date/datetime
                value_str = json.dumps(value, default=json_serializer)
            else:
                value_str = str(value) # Đảm bảo là string

            ttl = ttl or current_app.config['CACHE_TTL']
            redis_client.setex(key, ttl, value_str)
            print(f"Cache SET for key: {key} with TTL: {ttl}")
        except Exception as e:
            print(f"Lỗi set cache Redis (key: {key}): {e}")

def get_cache(key):
    """Lấy giá trị từ cache Redis."""
    redis_client = get_redis()
    if redis_client:
        try:
            value_str = redis_client.get(key)
            if value_str:
                print(f"Cache HIT for key: {key}")
                # Thử parse JSON
                try:
                    # Cần một hàm để parse ngược lại date/datetime nếu cần,
                    # nhưng thường thì trả về string ISO format là đủ cho API.
                    return json.loads(value_str)
                except json.JSONDecodeError:
                    return value_str # Trả về string nếu không phải JSON
            else:
                 print(f"Cache MISS for key: {key}")
                 return None
        except Exception as e:
            print(f"Lỗi get cache Redis (key: {key}): {e}")
            return None
    print(f"Cache MISS (Redis client unavailable) for key: {key}")
    return None

def delete_cache(key):
    """Xóa key khỏi cache Redis."""
    redis_client = get_redis()
    if redis_client:
        try:
            result = redis_client.delete(key)
            print(f"Cache DELETE for key: {key} - {'Success' if result > 0 else 'Key not found'}")
        except Exception as e:
            print(f"Lỗi delete cache Redis (key: {key}): {e}")

def delete_cache_pattern(pattern):
    """Xóa các keys theo một mẫu (ví dụ: 'sinhvien:*') - Cẩn thận khi dùng trên production."""
    redis_client = get_redis()
    if redis_client:
        try:
            deleted_count = 0
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)
                deleted_count += 1
            print(f"Cache DELETE for pattern: {pattern} - Deleted {deleted_count} keys")
        except Exception as e:
            print(f"Lỗi delete cache pattern Redis (pattern: {pattern}): {e}")