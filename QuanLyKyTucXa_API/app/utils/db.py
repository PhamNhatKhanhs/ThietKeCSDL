import mysql.connector.pooling
from flask import current_app, g

# Biến toàn cục để giữ pool connection
cnx_pool = None

def get_pool():
    """Khởi tạo hoặc trả về connection pool."""
    global cnx_pool
    if cnx_pool is None:
        try:
            print("Creating MySQL connection pool...")
            cnx_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=current_app.config['MYSQL_POOL_NAME'],
                pool_size=current_app.config['MYSQL_POOL_SIZE'],
                host=current_app.config['MYSQL_HOST'],
                user=current_app.config['MYSQL_USER'],
                password=current_app.config['MYSQL_PASSWORD'],
                database=current_app.config['MYSQL_DB']
            )
            print(f"MySQL connection pool '{cnx_pool.pool_name}' created successfully.")
        except mysql.connector.Error as err:
            print(f"Lỗi khi tạo MySQL connection pool: {err}")
            cnx_pool = None # Đảm bảo pool là None nếu có lỗi
    return cnx_pool

def get_db_connection():
    """Lấy một kết nối từ pool."""
    pool = get_pool()
    if pool:
        try:
            # Lấy connection từ pool
            # Lưu connection vào g để có thể đóng lại khi request kết thúc
            if 'db_conn' not in g:
                 g.db_conn = pool.get_connection()
            return g.db_conn
        except mysql.connector.Error as err:
            print(f"Lỗi khi lấy connection từ pool: {err}")
            return None
    return None

def close_db_connection(e=None):
    """Đóng connection và trả lại pool."""
    conn = g.pop('db_conn', None)
    if conn is not None:
        conn.close() # Trả connection về pool
        # print("MySQL connection returned to pool.")


def get_cursor(dictionary=True): # Bỏ named_tuple=False khỏi định nghĩa hàm
    """Lấy cursor từ connection hiện tại của request."""
    conn = get_db_connection()
    if conn:
        try:
            # Chỉ truyền tham số dictionary
            return conn.cursor(dictionary=dictionary)
        except mysql.connector.Error as err:
            print(f"Lỗi khi lấy cursor: {err}")
            return None
    return None

def init_app(app):
    """Đăng ký hàm teardown để đóng connection khi request kết thúc."""
    # Đảm bảo pool được tạo khi ứng dụng khởi động nếu cần
    with app.app_context():
        get_pool()
    app.teardown_appcontext(close_db_connection)