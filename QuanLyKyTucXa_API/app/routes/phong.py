# app/routes/phong.py
from flask import Blueprint, jsonify, request
from app.utils.db import get_cursor, get_db_connection
from app.utils.cache import get_cache, set_cache, delete_cache, delete_cache_pattern
import mysql.connector
from datetime import date # Import date
# Đảm bảo bạn đã tạo file này và hàm này hoạt động đúng
from app.services.phong_service import kiem_tra_phong_trong

bp = Blueprint('phong', __name__, url_prefix='/api') # Prefix chung /api

# --- API cho Loại Phòng ---

@bp.route('/loaiphong', methods=['GET'])
def get_all_loai_phong():
    """Lấy danh sách các loại phòng."""
    cache_key = "loaiphong:list"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("SELECT * FROM tblLoaiPhong ORDER BY maLoaiPhong")
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách loại phòng: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loaiphong/<string:maLoaiPhong>', methods=['GET'])
def get_loai_phong_by_id(maLoaiPhong):
    """Lấy chi tiết loại phòng."""
    cache_key = f"loaiphong:{maLoaiPhong}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("SELECT * FROM tblLoaiPhong WHERE maLoaiPhong = %s", (maLoaiPhong,))
        result = cursor.fetchone()
        if result:
            set_cache(cache_key, result)
            return jsonify(result)
        else:
            return jsonify({"message": "Không tìm thấy loại phòng"}), 404
    except Exception as e:
        print(f"Lỗi lấy chi tiết loại phòng {maLoaiPhong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loaiphong', methods=['POST'])
def create_loai_phong():
    """Tạo loại phòng mới."""
    data = request.get_json()
    if not data or not data.get('maLoaiPhong') or not data.get('tenLoai') or data.get('donGiaThang') is None or data.get('sucChua') is None:
        return jsonify({"error": "Thiếu thông tin bắt buộc (maLoaiPhong, tenLoai, donGiaThang, sucChua)"}), 400

    sql = "INSERT INTO tblLoaiPhong (maLoaiPhong, tenLoai, donGiaThang, sucChua, moTa) VALUES (%s, %s, %s, %s, %s)"
    params = (data['maLoaiPhong'], data['tenLoai'], data['donGiaThang'], data['sucChua'], data.get('moTa'))

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, params)
        db_conn.commit()
        delete_cache("loaiphong:list") # Xóa cache list
        # Trả về dữ liệu vừa tạo
        cursor_get = get_cursor(dictionary=True)
        cursor_get.execute("SELECT * FROM tblLoaiPhong WHERE maLoaiPhong = %s", (data['maLoaiPhong'],))
        new_loai_phong = cursor_get.fetchone()
        cursor_get.close()
        return jsonify({"message": "Tạo loại phòng thành công", "loaiPhong": new_loai_phong}), 201
    except mysql.connector.IntegrityError:
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Mã loại phòng đã tồn tại"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi tạo loại phòng: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loaiphong/<string:maLoaiPhong>', methods=['PUT'])
def update_loai_phong(maLoaiPhong):
    """Cập nhật thông tin loại phòng."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Không có dữ liệu cập nhật"}), 400

    set_clauses = []
    params = []
    allowed_fields = ['tenLoai', 'donGiaThang', 'sucChua', 'moTa']

    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses:
        return jsonify({"error": "Không có trường hợp lệ để cập nhật"}), 400

    params.append(maLoaiPhong)
    query = f"UPDATE tblLoaiPhong SET {', '.join(set_clauses)} WHERE maLoaiPhong = %s"

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        cursor.execute(query, tuple(params))

        if cursor.rowcount == 0:
            return jsonify({"message": f"Không tìm thấy loại phòng {maLoaiPhong}"}), 404

        db_conn.commit()
        delete_cache(f"loaiphong:{maLoaiPhong}") # Xóa cache chi tiết
        delete_cache("loaiphong:list")        # Xóa cache list
        # Xóa cache các phòng thuộc loại này (vì donGiaThang, sucChua có thể thay đổi)
        delete_cache_pattern(f"phong:*") # Xóa cache tất cả các phòng
        delete_cache("phong:list")

        return jsonify({"message": f"Cập nhật loại phòng {maLoaiPhong} thành công"}), 200
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật loại phòng {maLoaiPhong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loaiphong/<string:maLoaiPhong>', methods=['DELETE'])
def delete_loai_phong(maLoaiPhong):
    """Xóa một loại phòng."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        cursor.execute("DELETE FROM tblLoaiPhong WHERE maLoaiPhong = %s", (maLoaiPhong,))

        if cursor.rowcount == 0:
            return jsonify({"message": f"Không tìm thấy loại phòng {maLoaiPhong}"}), 404

        db_conn.commit()
        delete_cache(f"loaiphong:{maLoaiPhong}")
        delete_cache("loaiphong:list")
        # Xóa cache các phòng thuộc loại này
        delete_cache_pattern(f"phong:*")
        delete_cache("phong:list")

        return jsonify({"message": f"Xóa loại phòng {maLoaiPhong} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        # Lỗi nếu còn phòng đang sử dụng loại phòng này (do ON DELETE RESTRICT)
        if db_conn: db_conn.rollback()
        print(f"Lỗi FK khi xóa loại phòng {maLoaiPhong}: {e}")
        return jsonify({"error": "Không thể xóa loại phòng vì còn phòng đang sử dụng"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa loại phòng {maLoaiPhong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

# --- API cho Phòng ---

@bp.route('/phong', methods=['GET'])
def get_all_phong():
    """Lấy danh sách các phòng."""
    cache_key = "phong:list"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("""
            SELECT p.maPhong, p.soPhong, p.trangThai, lp.maLoaiPhong, lp.tenLoai, lp.donGiaThang, lp.sucChua
            FROM tblPhong p
            JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
            ORDER BY p.soPhong
        """)
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách phòng: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/phong/<string:maPhong>', methods=['GET'])
def get_phong_by_id(maPhong):
    """Lấy chi tiết phòng."""
    cache_key = f"phong:{maPhong}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("""
            SELECT p.maPhong, p.soPhong, p.trangThai, lp.maLoaiPhong, lp.tenLoai, lp.donGiaThang, lp.sucChua, lp.moTa
            FROM tblPhong p
            JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
            WHERE p.maPhong = %s
        """, (maPhong,))
        result = cursor.fetchone()
        if result:
            set_cache(cache_key, result)
            return jsonify(result)
        else:
            return jsonify({"message": "Không tìm thấy phòng"}), 404
    except Exception as e:
        print(f"Lỗi lấy chi tiết phòng {maPhong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/phong', methods=['POST'])
def create_phong():
    """Tạo phòng mới."""
    data = request.get_json()
    if not data or not data.get('maPhong') or not data.get('soPhong') or not data.get('maLoaiPhong'):
        return jsonify({"error": "Thiếu thông tin bắt buộc (maPhong, soPhong, maLoaiPhong)"}), 400

    sql = "INSERT INTO tblPhong (maPhong, soPhong, maLoaiPhong, trangThai) VALUES (%s, %s, %s, %s)"
    params = (data['maPhong'], data['soPhong'], data['maLoaiPhong'], data.get('trangThai', 'Sẵn sàng'))

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, params)
        db_conn.commit()
        delete_cache("phong:list") # Xóa cache list
        # Lấy lại thông tin phòng vừa tạo để trả về (bao gồm cả loại phòng)
        cursor_get = get_cursor(dictionary=True)
        cursor_get.execute("""
             SELECT p.maPhong, p.soPhong, p.trangThai, lp.maLoaiPhong, lp.tenLoai, lp.donGiaThang, lp.sucChua
             FROM tblPhong p JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
             WHERE p.maPhong = %s
         """, (data['maPhong'],))
        new_phong = cursor_get.fetchone()
        cursor_get.close()
        return jsonify({"message": "Tạo phòng thành công", "phong": new_phong}), 201
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        err_msg = str(e)
        field = "Mã phòng" if "PRIMARY" in err_msg else "Số phòng" if "soPhong" in err_msg else "Mã loại phòng" if "maLoaiPhong" in err_msg else "Khóa"
        return jsonify({"error": f"{field} đã tồn tại hoặc không hợp lệ."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi tạo phòng: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/phong/<string:maPhong>', methods=['PUT'])
def update_phong(maPhong):
    """Cập nhật thông tin phòng (ví dụ: trạng thái, loại phòng)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Không có dữ liệu cập nhật"}), 400

    set_clauses = []
    params = []
    # Chỉ cho phép cập nhật một số trường nhất định
    allowed_fields = ['soPhong', 'maLoaiPhong', 'trangThai']

    for field in allowed_fields:
         if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses:
        return jsonify({"error": "Không có trường hợp lệ để cập nhật"}), 400

    params.append(maPhong)
    query = f"UPDATE tblPhong SET {', '.join(set_clauses)} WHERE maPhong = %s"

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        cursor.execute(query, tuple(params))

        if cursor.rowcount == 0:
            return jsonify({"message": f"Không tìm thấy phòng {maPhong}"}), 404

        db_conn.commit()
        delete_cache(f"phong:{maPhong}")
        delete_cache("phong:list")

        return jsonify({"message": f"Cập nhật phòng {maPhong} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        # Lỗi nếu cập nhật trùng soPhong hoặc maLoaiPhong không tồn tại
        if db_conn: db_conn.rollback()
        err_msg = str(e)
        field = "Số phòng" if "soPhong" in err_msg else "Mã loại phòng" if "maLoaiPhong" in err_msg else "Khóa"
        return jsonify({"error": f"{field} đã tồn tại hoặc không hợp lệ."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật phòng {maPhong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/phong/<string:maPhong>', methods=['DELETE'])
def delete_phong(maPhong):
    """Xóa một phòng."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        cursor.execute("DELETE FROM tblPhong WHERE maPhong = %s", (maPhong,))

        if cursor.rowcount == 0:
            return jsonify({"message": f"Không tìm thấy phòng {maPhong}"}), 404

        db_conn.commit()
        delete_cache(f"phong:{maPhong}")
        delete_cache("phong:list")

        return jsonify({"message": f"Xóa phòng {maPhong} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        # Lỗi nếu còn hợp đồng thuộc phòng này (do ON DELETE RESTRICT)
        if db_conn: db_conn.rollback()
        print(f"Lỗi FK khi xóa phòng {maPhong}: {e}")
        return jsonify({"error": "Không thể xóa phòng vì còn hợp đồng đang liên kết"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa phòng {maPhong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


# --- API cho Hợp đồng Thuê phòng ---

@bp.route('/hopdong', methods=['POST'])
def create_hop_dong():
    """Tạo hợp đồng thuê phòng mới."""
    data = request.get_json()
    if not data or not data.get('maHopDong') or not data.get('maSV') or not data.get('maPhong') or not data.get('ngayBatDau'):
         return jsonify({"error": "Thiếu thông tin bắt buộc (maHopDong, maSV, maPhong, ngayBatDau)"}), 400

    maPhong = data['maPhong']
    maSV = data['maSV'] # Lấy mã SV để kiểm tra hợp đồng khác nếu cần

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        # Tắt autocommit để kiểm tra và insert trong cùng transaction
        db_conn.autocommit = False
        cursor = db_conn.cursor(dictionary=True) # Dùng dict để lấy kết quả kiểm tra
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # 1. Kiểm tra phòng trống (Gọi Service)
        is_available, message, _ = kiem_tra_phong_trong(maPhong)
        if not is_available:
             db_conn.rollback() # Rollback trước khi trả về lỗi
             db_conn.autocommit = True
             if cursor: cursor.close()
             return jsonify({"error": message}), 409 # 409 Conflict - Phòng đầy hoặc lỗi service

        # 2. (Tùy chọn) Kiểm tra xem sinh viên này còn hợp đồng nào đang thuê không
        cursor.execute("SELECT maHopDong FROM tblHopDongThuePhong WHERE maSV = %s AND trangThai = 'Đang thuê'", (maSV,))
        hop_dong_khac = cursor.fetchone()
        if hop_dong_khac:
            db_conn.rollback()
            db_conn.autocommit = True
            if cursor: cursor.close()
            return jsonify({"error": f"Sinh viên {maSV} đã có hợp đồng {hop_dong_khac['maHopDong']} đang thuê."}), 409


        # 3. Nếu mọi kiểm tra OK, tiến hành INSERT
        cursor_insert = db_conn.cursor() # Dùng cursor thường để insert
        sql = """
            INSERT INTO tblHopDongThuePhong
            (maHopDong, maSV, maPhong, ngayBatDau, ngayKetThuc, tienCoc, trangThai)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['maHopDong'], maSV, maPhong, data['ngayBatDau'],
            data.get('ngayKetThuc'), data.get('tienCoc', 0), data.get('trangThai', 'Đang thuê')
        )
        cursor_insert.execute(sql, params)
        cursor_insert.close() # Đóng cursor insert

        db_conn.commit() # Commit transaction thành công

        # Xóa cache liên quan
        delete_cache(f"phong:{maPhong}")
        delete_cache("phong:list")

        return jsonify({"message": "Tạo hợp đồng thành công", "hopDong": data}), 201

    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        err_msg = str(e)
        field = "Mã hợp đồng" if "PRIMARY" in err_msg else "Mã SV hoặc Mã phòng" if "FOREIGN KEY" in err_msg else "Khóa"
        return jsonify({"error": f"{field} đã tồn tại hoặc không hợp lệ."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi tạo hợp đồng: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if db_conn: db_conn.autocommit = True # Bật lại autocommit
        if cursor: cursor.close() # Đóng cursor chính


@bp.route('/sinhvien/<string:maSV>/hopdong', methods=['GET'])
def get_hop_dong_by_sv(maSV):
    """Lấy danh sách hợp đồng của một sinh viên."""
    # Có thể cache nhưng hợp đồng ít thay đổi, tùy nhu cầu
    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("""
            SELECT hd.*, p.soPhong, lp.tenLoai
            FROM tblHopDongThuePhong hd
            JOIN tblPhong p ON hd.maPhong = p.maPhong
            JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
            WHERE hd.maSV = %s
            ORDER BY hd.ngayBatDau DESC
        """, (maSV,))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy hợp đồng của SV {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


@bp.route('/hopdong/<string:maHopDong>', methods=['PUT'])
def update_hop_dong(maHopDong):
    """Cập nhật hợp đồng (ví dụ: ngày kết thúc, trạng thái)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Không có dữ liệu cập nhật"}), 400

    set_clauses = []
    params = []
    # Các trường thường được cập nhật
    allowed_fields = ['ngayKetThuc', 'tienCoc', 'trangThai']

    for field in allowed_fields:
         if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses:
        return jsonify({"error": "Không có trường hợp lệ để cập nhật"}), 400

    params.append(maHopDong)
    query = f"UPDATE tblHopDongThuePhong SET {', '.join(set_clauses)} WHERE maHopDong = %s"

    cursor = None
    db_conn = None
    maPhong = None # Biến để lưu mã phòng nếu cần xóa cache
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True) # Dùng dict để lấy mã phòng
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # Lấy mã phòng trước khi cập nhật để xóa cache nếu trạng thái thay đổi
        cursor.execute("SELECT maPhong, trangThai FROM tblHopDongThuePhong WHERE maHopDong = %s", (maHopDong,))
        hop_dong_hien_tai = cursor.fetchone()
        if not hop_dong_hien_tai:
             return jsonify({"message": f"Không tìm thấy hợp đồng {maHopDong}"}), 404
        maPhong = hop_dong_hien_tai['maPhong']
        trangThaiCu = hop_dong_hien_tai['trangThai']

        # Thực hiện cập nhật
        cursor_update = db_conn.cursor()
        cursor_update.execute(query, tuple(params))
        cursor_update.close()

        if cursor_update.rowcount == 0:
            # Trường hợp này ít xảy ra vì đã kiểm tra tồn tại ở trên
            return jsonify({"message": f"Không tìm thấy hợp đồng {maHopDong} để cập nhật"}), 404

        db_conn.commit()

        # Xóa cache nếu cần
        trangThaiMoi = data.get('trangThai', trangThaiCu)
        if trangThaiMoi != trangThaiCu and maPhong: # Nếu trạng thái thay đổi
            delete_cache(f"phong:{maPhong}")
            delete_cache("phong:list")

        return jsonify({"message": f"Cập nhật hợp đồng {maHopDong} thành công"}), 200

    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật hợp đồng {maHopDong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


@bp.route('/hopdong/<string:maHopDong>', methods=['DELETE'])
def delete_hop_dong(maHopDong):
    """Xóa một hợp đồng (cân nhắc dùng PUT để đổi trạng thái thay vì xóa)."""
    cursor = None
    db_conn = None
    maPhong = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True) # Dùng dict để lấy mã phòng
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # Lấy mã phòng trước khi xóa để xóa cache
        cursor.execute("SELECT maPhong FROM tblHopDongThuePhong WHERE maHopDong = %s", (maHopDong,))
        hop_dong = cursor.fetchone()
        if not hop_dong:
             return jsonify({"message": f"Không tìm thấy hợp đồng {maHopDong}"}), 404
        maPhong = hop_dong['maPhong']

        # Thực hiện xóa
        cursor_delete = db_conn.cursor()
        cursor_delete.execute("DELETE FROM tblHopDongThuePhong WHERE maHopDong = %s", (maHopDong,))
        cursor_delete.close()

        if cursor_delete.rowcount == 0:
             return jsonify({"message": f"Không tìm thấy hợp đồng {maHopDong} để xóa"}), 404

        db_conn.commit()

        # Xóa cache liên quan đến phòng
        if maPhong:
            delete_cache(f"phong:{maPhong}")
            delete_cache("phong:list")

        return jsonify({"message": f"Xóa hợp đồng {maHopDong} thành công"}), 200
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa hợp đồng {maHopDong}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()