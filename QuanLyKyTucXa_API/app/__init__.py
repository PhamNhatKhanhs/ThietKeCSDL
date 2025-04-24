from flask import Flask, jsonify
from .config import Config
from .utils import db as db_utils
# Không cần import cache_utils ở đây vì nó dùng 'g'

def create_app():
    """Factory function để tạo và cấu hình Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Khởi tạo tiện ích DB (đăng ký teardown)
    db_utils.init_app(app)

    # Đăng ký Blueprints cho các routes API
    from .routes import sinh_vien, phong, dich_vu, gui_xe, khach, hoa_don, bao_cao # Import các module route
    app.register_blueprint(sinh_vien.bp)
    app.register_blueprint(phong.bp)
    app.register_blueprint(dich_vu.bp)
    app.register_blueprint(gui_xe.bp)
    app.register_blueprint(khach.bp)
    app.register_blueprint(hoa_don.bp)
    app.register_blueprint(bao_cao.bp)

    # Endpoint kiểm tra sức khỏe hệ thống
    @app.route('/health')
    def health_check():
        db_status = "disconnected"
        redis_status = "disconnected"
        # Kiểm tra DB bằng cách thử lấy connection
        conn = None
        cursor = None
        try:
            conn = db_utils.get_db_connection()
            if conn and conn.is_connected():
                 cursor = conn.cursor()
                 cursor.execute("SELECT 1")
                 cursor.fetchone()
                 db_status = "connected"
        except Exception as e:
            print(f"Health check DB Error: {e}")
        finally:
             if cursor: cursor.close()
             # Không đóng conn ở đây vì teardown sẽ xử lý

        # Kiểm tra Redis
        try:
            # Import get_redis trực tiếp ở đây thay vì dùng global
            from .utils.cache import get_redis
            with app.app_context(): # Cần app context để truy cập 'g'
                redis_client = get_redis()
                if redis_client and redis_client.ping():
                    redis_status = "connected"
        except Exception as e:
             print(f"Health check Redis Error: {e}")

        return jsonify({"database": db_status, "cache": redis_status})

    print("Flask app created successfully.")
    return app