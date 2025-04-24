import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv()

class Config:
    """Lớp cấu hình cho ứng dụng Flask."""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a-default-very-secret-key' # Cần thiết cho session, flash,...

    # Cấu hình MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    # Cấu hình connection pool (tùy chọn nhưng nên có cho ứng dụng thực tế)
    MYSQL_POOL_NAME = "mysql_pool"
    MYSQL_POOL_SIZE = 5 # Số lượng kết nối tối đa trong pool

    # Cấu hình Redis
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    # Thời gian sống mặc định cho cache (ví dụ: 1 giờ)
    CACHE_TTL = 3600