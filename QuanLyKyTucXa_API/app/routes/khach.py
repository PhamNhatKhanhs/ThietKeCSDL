# app/routes/khach.py
from flask import Blueprint, jsonify, request
from app.utils.db import get_cursor, get_db_connection
from app.utils.cache import get_cache, set_cache, delete_cache, delete_cache_pattern
import mysql.connector
from datetime import datetime

bp = Blueprint('khach', __name__, url_prefix='/api/khach')

# --- API cho Khách ---
@bp.route('/', methods=['GET'])
def get_all_khach():
    """Lấy danh sách khách."""
    cache_key = "khach:list"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("SELECT * FROM tblKhach ORDER BY hoTen")
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách khách: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/<int:maKhach>', methods=['GET'])
def get_khach_by_id(maKhach):
    """Lấy chi tiết khách."""
    cache_key = f"khach:{maKhach}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("SELECT * FROM tblKhach WHERE maKhach = %s", (maKhach,))
        result = cursor.fetchone()
        if result:
            set_cache(cache_key, result)
            return jsonify(result)
        else:
            return jsonify({"message":"Không tìm thấy khách"}), 404
    except Exception as e:
        print(f"Lỗi lấy chi tiết khách {maKhach}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/', methods=['POST'])
def create_khach():
    """Tạo khách mới (ít dùng, thường tạo qua API thăm)."""
    data = request.get_json()
    if not data or not data.get('hoTen'): # Chỉ cần họ tên là đủ? Thêm CMT nếu muốn unique
        return jsonify({"error": "Thiếu thông tin bắt buộc (hoTen)"}), 400

    sql = "INSERT INTO tblKhach (hoTen, soCMT, ngaySinh) VALUES (%s, %s, %s)"
    params = (data['hoTen'], data.get('soCMT'), data.get('ngaySinh'))

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, params)
        new_id = cursor.lastrowid
        db_conn.commit()
        delete_cache("khach:list")
        # Lấy lại thông tin khách vừa tạo
        cursor_get = get_cursor(dictionary=True)
        cursor_get.execute("SELECT * FROM tblKhach WHERE maKhach = %s", (new_id,))
        new_khach = cursor_get.fetchone()
        cursor_get.close()
        return jsonify({"message": "Tạo khách thành công", "khach": new_khach}), 201
    except mysql.connector.IntegrityError as e:
        # Lỗi nếu soCMT là UNIQUE và bị trùng
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Số CMT đã tồn tại (nếu là UNIQUE)."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi tạo khách: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/<int:maKhach>', methods=['PUT'])
def update_khach(maKhach):
    """Cập nhật thông tin khách."""
    data = request.get_json()
    if not data: return jsonify({"error": "Không có dữ liệu cập nhật"}), 400

    set_clauses = []
    params = []
    allowed_fields = ['hoTen', 'soCMT', 'ngaySinh']
    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses: return jsonify({"error": "Không có trường hợp lệ để cập nhật"}), 400

    params.append(maKhach)
    query = f"UPDATE tblKhach SET {', '.join(set_clauses)} WHERE maKhach = %s"
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(query, tuple(params))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy khách {maKhach}"}), 404
        db_conn.commit()
        delete_cache(f"khach:{maKhach}")
        delete_cache("khach:list")
        return jsonify({"message": f"Cập nhật khách {maKhach} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Số CMT đã tồn tại (nếu là UNIQUE)."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật khách {maKhach}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/<int:maKhach>', methods=['DELETE'])
def delete_khach(maKhach):
    """Xóa một khách."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("DELETE FROM tblKhach WHERE maKhach = %s", (maKhach,))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy khách {maKhach}"}), 404
        db_conn.commit()
        delete_cache(f"khach:{maKhach}")
        delete_cache("khach:list")
        return jsonify({"message": f"Xóa khách {maKhach} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        # Lỗi nếu còn lượt thăm liên kết (FK nên là ON DELETE CASCADE trong tblThamKhach)
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Không thể xóa khách vì còn lượt thăm liên quan"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa khách {maKhach}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

# --- API cho Lượt Thăm ---
@bp.route('/tham', methods=['POST'])
def add_tham_khach():
    """Ghi nhận một lượt khách vào thăm."""
    data = request.get_json()
    if not data or not data.get('maSV'):
        return jsonify({"error": "Thiếu thông tin bắt buộc (maSV và thông tin khách)"}), 400

    maSV = data['maSV']
    maKhach = data.get('maKhach')
    thoiGianVao = data.get('thoiGianVao', datetime.now().isoformat())
    ghiChu = data.get('ghiChu')

    db_conn = get_db_connection() # Lấy connection dùng chung
    if not db_conn: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

    try:
        db_conn.autocommit = False # Bắt đầu transaction

        # Nếu không cung cấp maKhach, cần tìm hoặc tạo khách mới
        if not maKhach:
            hoTenKhach = data.get('hoTenKhach')
            soCMTKhach = data.get('soCMTKhach')
            ngaySinhKhach = data.get('ngaySinhKhach')
            # Nên yêu cầu cả họ tên và CMT để tìm/tạo cho chính xác
            if not hoTenKhach or not soCMTKhach:
                 raise ValueError("Thiếu họ tên hoặc số CMT của khách khi không có mã khách")

            cursor_find = db_conn.cursor(dictionary=True)
            cursor_find.execute("SELECT maKhach FROM tblKhach WHERE soCMT = %s", (soCMTKhach,))
            khach = cursor_find.fetchone()
            cursor_find.close() # Đóng cursor tìm kiếm

            if khach:
                maKhach = khach['maKhach']
            else:
                # Chưa có khách này -> Tạo mới
                cursor_create = db_conn.cursor()
                sql_create = "INSERT INTO tblKhach (hoTen, soCMT, ngaySinh) VALUES (%s, %s, %s)"
                cursor_create.execute(sql_create, (hoTenKhach, soCMTKhach, ngaySinhKhach))
                maKhach = cursor_create.lastrowid # Lấy ID khách vừa tạo
                cursor_create.close() # Đóng cursor tạo
                print(f"Đã tạo khách mới: {maKhach}")
                delete_cache("khach:list") # Xóa cache list khách

        # Giờ đã có maKhach, tiến hành ghi nhận lượt thăm
        sql_insert_tham = "INSERT INTO tblThamKhach (maKhach, maSV, thoiGianVao, ghiChu) VALUES (%s, %s, %s, %s)"
        params_tham = (maKhach, maSV, thoiGianVao, ghiChu)
        cursor_tham = db_conn.cursor()
        cursor_tham.execute(sql_insert_tham, params_tham)
        maThamMoi = cursor_tham.lastrowid
        cursor_tham.close()

        db_conn.commit() # Commit thành công cả việc tạo khách (nếu có) và lượt thăm

        return jsonify({
            "message": "Ghi nhận lượt thăm thành công",
            "maTham": maThamMoi
        }), 201

    except ValueError as ve: # Bắt lỗi validate tự định nghĩa
        if db_conn: db_conn.rollback()
        return jsonify({"error": str(ve)}), 400
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        # Lỗi FK nếu maSV không tồn tại hoặc lỗi UNIQUE nếu có
        return jsonify({"error": "Mã sinh viên không hợp lệ hoặc lỗi ràng buộc CSDL."}), 400
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi ghi nhận lượt thăm: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
         if db_conn: db_conn.autocommit = True # Bật lại autocommit


@bp.route('/tham/<int:maTham>/ra', methods=['PUT'])
def update_tham_khach_ra(maTham):
    """Ghi nhận thời gian khách ra."""
    thoiGianRa = datetime.now().isoformat() # Lấy thời gian hiện tại

    sql = "UPDATE tblThamKhach SET thoiGianRa = %s WHERE maTham = %s AND thoiGianRa IS NULL"

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True) # Dùng dict để kiểm tra sau
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        cursor_update = db_conn.cursor()
        cursor_update.execute(sql, (thoiGianRa, maTham))
        rowcount = cursor_update.rowcount # Lưu lại số dòng ảnh hưởng
        cursor_update.close()

        if rowcount == 0:
             # Kiểm tra xem mã thăm có tồn tại không hoặc đã ghi nhận ra rồi
             cursor.execute("SELECT thoiGianRa FROM tblThamKhach WHERE maTham = %s", (maTham,))
             tham = cursor.fetchone()
             if not tham:
                 return jsonify({"message": f"Không tìm thấy lượt thăm với mã {maTham}"}), 404
             elif tham['thoiGianRa'] is not None:
                 return jsonify({"message": f"Lượt thăm {maTham} đã được ghi nhận ra trước đó"}), 400
             else: # Lỗi không xác định
                 return jsonify({"error":"Không thể cập nhật trạng thái"}), 500

        db_conn.commit()
        return jsonify({"message": f"Đã ghi nhận khách ra cho lượt thăm {maTham}"}), 200
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật thời gian ra: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


@bp.route('/sinhvien/<string:maSV>/tham', methods=['GET'])
def get_tham_khach_by_sv(maSV):
    """Lấy lịch sử khách thăm của sinh viên."""
    tuNgay = request.args.get('tuNgay')
    denNgay = request.args.get('denNgay')

    sql = """
        SELECT tk.maTham, tk.maKhach, k.hoTen AS tenKhach, k.soCMT, tk.thoiGianVao, tk.thoiGianRa, tk.ghiChu
        FROM tblThamKhach tk
        JOIN tblKhach k ON tk.maKhach = k.maKhach
        WHERE tk.maSV = %s
    """
    params = [maSV]
    if tuNgay:
        sql += " AND tk.thoiGianVao >= %s"
        params.append(f"{tuNgay} 00:00:00") # Bắt đầu từ 0h ngày đó
    if denNgay:
        # Lấy đến hết ngày đó
        try:
            end_date_obj = datetime.fromisoformat(denNgay).date()
            next_day = end_date_obj + timedelta(days=1)
            sql += " AND tk.thoiGianVao < %s"
            params.append(next_day.isoformat())
        except ValueError:
             return jsonify({"error": "Định dạng denNgay không hợp lệ (YYYY-MM-DD)"}), 400

    sql += " ORDER BY tk.thoiGianVao DESC"

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, tuple(params))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy lịch sử thăm khách của SV {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()