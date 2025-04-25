# app/routes/dich_vu.py
from flask import Blueprint, jsonify, request
from app.utils.db import get_cursor, get_db_connection
from app.utils.cache import get_cache, set_cache, delete_cache, delete_cache_pattern
import mysql.connector
from datetime import datetime, timedelta # Import datetime và timedelta

bp = Blueprint('dich_vu', __name__, url_prefix='/api/dichvu')

# --- API cho Loại Dịch Vụ ---
@bp.route('/loai', methods=['GET'])
def get_all_loai_dich_vu():
    """Lấy danh sách loại dịch vụ."""
    cache_key = "loaidichvu:list"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("SELECT * FROM tblLoaiDichVu ORDER BY maLoaiDV")
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách loại dịch vụ: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loai/<string:maLoaiDV>', methods=['GET'])
def get_loai_dich_vu_by_id(maLoaiDV):
    """Lấy chi tiết loại dịch vụ."""
    cache_key = f"loaidichvu:{maLoaiDV}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("SELECT * FROM tblLoaiDichVu WHERE maLoaiDV = %s", (maLoaiDV,))
        result = cursor.fetchone()
        if result:
            set_cache(cache_key, result)
            return jsonify(result)
        else:
            return jsonify({"message":"Không tìm thấy loại dịch vụ"}), 404
    except Exception as e:
        print(f"Lỗi lấy chi tiết loại dịch vụ {maLoaiDV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loai', methods=['POST'])
def create_loai_dich_vu():
    """Tạo loại dịch vụ mới."""
    data = request.get_json()
    if not data or not data.get('maLoaiDV') or not data.get('tenLoaiDV'):
        return jsonify({"error": "Thiếu thông tin bắt buộc (maLoaiDV, tenLoaiDV)"}), 400

    sql = "INSERT INTO tblLoaiDichVu (maLoaiDV, tenLoaiDV, moTa) VALUES (%s, %s, %s)"
    params = (data['maLoaiDV'], data['tenLoaiDV'], data.get('moTa'))

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, params)
        db_conn.commit()
        delete_cache("loaidichvu:list")
        return jsonify({"message": "Tạo loại dịch vụ thành công", "loaiDichVu": data}), 201
    except mysql.connector.IntegrityError:
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Mã loại dịch vụ đã tồn tại"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi tạo loại dịch vụ: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loai/<string:maLoaiDV>', methods=['PUT'])
def update_loai_dich_vu(maLoaiDV):
    """Cập nhật loại dịch vụ."""
    data = request.get_json()
    if not data: return jsonify({"error": "Không có dữ liệu cập nhật"}), 400

    set_clauses = []
    params = []
    allowed_fields = ['tenLoaiDV', 'moTa']
    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses: return jsonify({"error": "Không có trường hợp lệ để cập nhật"}), 400

    params.append(maLoaiDV)
    query = f"UPDATE tblLoaiDichVu SET {', '.join(set_clauses)} WHERE maLoaiDV = %s"
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(query, tuple(params))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy loại dịch vụ {maLoaiDV}"}), 404
        db_conn.commit()
        delete_cache(f"loaidichvu:{maLoaiDV}")
        delete_cache("loaidichvu:list")
        # Xóa cache các dịch vụ thuộc loại này nếu cần
        delete_cache_pattern("dichvu:*")
        delete_cache("dichvu:list")
        return jsonify({"message": f"Cập nhật loại dịch vụ {maLoaiDV} thành công"}), 200
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật loại dịch vụ {maLoaiDV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/loai/<string:maLoaiDV>', methods=['DELETE'])
def delete_loai_dich_vu(maLoaiDV):
    """Xóa loại dịch vụ."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("DELETE FROM tblLoaiDichVu WHERE maLoaiDV = %s", (maLoaiDV,))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy loại dịch vụ {maLoaiDV}"}), 404
        db_conn.commit()
        delete_cache(f"loaidichvu:{maLoaiDV}")
        delete_cache("loaidichvu:list")
        delete_cache_pattern("dichvu:*")
        delete_cache("dichvu:list")
        return jsonify({"message": f"Xóa loại dịch vụ {maLoaiDV} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Không thể xóa loại dịch vụ vì còn dịch vụ đang sử dụng"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa loại dịch vụ {maLoaiDV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


# --- API cho Dịch Vụ ---
@bp.route('/', methods=['GET'])
def get_all_dich_vu():
    """Lấy danh sách dịch vụ."""
    cache_key = "dichvu:list"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("""
            SELECT dv.*, ldv.tenLoaiDV
            FROM tblDichVu dv
            JOIN tblLoaiDichVu ldv ON dv.maLoaiDV = ldv.maLoaiDV
            ORDER BY dv.maLoaiDV, dv.tenDV
        """)
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách dịch vụ: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/<string:maDV>', methods=['GET'])
def get_dich_vu_by_id(maDV):
    """Lấy chi tiết dịch vụ."""
    cache_key = f"dichvu:{maDV}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("""
            SELECT dv.*, ldv.tenLoaiDV
            FROM tblDichVu dv
            JOIN tblLoaiDichVu ldv ON dv.maLoaiDV = ldv.maLoaiDV
            WHERE dv.maDV = %s
        """,(maDV,))
        result = cursor.fetchone()
        if result:
            set_cache(cache_key, result)
            return jsonify(result)
        else:
            return jsonify({"message":"Không tìm thấy dịch vụ"}), 404
    except Exception as e:
        print(f"Lỗi lấy chi tiết dịch vụ {maDV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/', methods=['POST'])
def create_dich_vu():
    """Tạo dịch vụ mới."""
    data = request.get_json()
    if not data or not data.get('maDV') or not data.get('maLoaiDV') or not data.get('tenDV') or data.get('donGia') is None:
         return jsonify({"error": "Thiếu thông tin bắt buộc (maDV, maLoaiDV, tenDV, donGia)"}), 400

    sql = "INSERT INTO tblDichVu (maDV, maLoaiDV, tenDV, donGia, donViTinh) VALUES (%s, %s, %s, %s, %s)"
    params = (data['maDV'], data['maLoaiDV'], data['tenDV'], data['donGia'], data.get('donViTinh'))

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, params)
        db_conn.commit()
        delete_cache("dichvu:list")
        # Lấy lại thông tin vừa tạo
        cursor_get = get_cursor(dictionary=True)
        cursor_get.execute("""
             SELECT dv.*, ldv.tenLoaiDV FROM tblDichVu dv
             JOIN tblLoaiDichVu ldv ON dv.maLoaiDV = ldv.maLoaiDV WHERE dv.maDV = %s
        """, (data['maDV'],))
        new_dv = cursor_get.fetchone()
        cursor_get.close()
        return jsonify({"message": "Tạo dịch vụ thành công", "dichVu": new_dv}), 201
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        err_msg = str(e)
        field = "Mã dịch vụ" if "PRIMARY" in err_msg else "Tên dịch vụ" if "tenDV" in err_msg else "Mã loại dịch vụ" if "maLoaiDV" in err_msg else "Khóa"
        return jsonify({"error": f"{field} đã tồn tại hoặc không hợp lệ."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi tạo dịch vụ: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


@bp.route('/<string:maDV>', methods=['PUT'])
def update_dich_vu(maDV):
    """Cập nhật dịch vụ."""
    data = request.get_json()
    if not data: return jsonify({"error": "Không có dữ liệu cập nhật"}), 400

    set_clauses = []
    params = []
    allowed_fields = ['maLoaiDV', 'tenDV', 'donGia', 'donViTinh']
    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses: return jsonify({"error": "Không có trường hợp lệ để cập nhật"}), 400

    params.append(maDV)
    query = f"UPDATE tblDichVu SET {', '.join(set_clauses)} WHERE maDV = %s"
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(query, tuple(params))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy dịch vụ {maDV}"}), 404
        db_conn.commit()
        delete_cache(f"dichvu:{maDV}")
        delete_cache("dichvu:list")
        return jsonify({"message": f"Cập nhật dịch vụ {maDV} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        err_msg = str(e)
        field = "Tên dịch vụ" if "tenDV" in err_msg else "Mã loại dịch vụ" if "maLoaiDV" in err_msg else "Khóa"
        return jsonify({"error": f"{field} đã tồn tại hoặc không hợp lệ."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật dịch vụ {maDV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/<string:maDV>', methods=['DELETE'])
def delete_dich_vu(maDV):
    """Xóa một dịch vụ."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("DELETE FROM tblDichVu WHERE maDV = %s", (maDV,))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy dịch vụ {maDV}"}), 404
        db_conn.commit()
        delete_cache(f"dichvu:{maDV}")
        delete_cache("dichvu:list")
        return jsonify({"message": f"Xóa dịch vụ {maDV} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        # Lỗi nếu còn bản ghi sử dụng dịch vụ này
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Không thể xóa dịch vụ vì đã có người sử dụng"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa dịch vụ {maDV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


# --- API cho Sử dụng Dịch Vụ ---

@bp.route('/sudung', methods=['POST'])
def add_su_dung_dich_vu():
    """Ghi nhận một lượt sử dụng dịch vụ của sinh viên."""
    data = request.get_json()
    if not data or not data.get('maSV') or not data.get('maDV'):
        return jsonify({"error": "Thiếu thông tin bắt buộc (maSV, maDV)"}), 400

    maSV = data['maSV']
    maDV = data['maDV']
    soLuong = data.get('soLuong', 1) # Mặc định số lượng là 1
    try:
        soLuong = int(soLuong)
        if soLuong <= 0: raise ValueError("Số lượng phải lớn hơn 0")
    except ValueError as e:
         return jsonify({"error": f"Số lượng không hợp lệ: {e}"}), 400

    thoiGianSuDung = data.get('thoiGianSuDung', datetime.now().isoformat()) # Lấy thời gian hiện tại nếu không cung cấp

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # 1. Lấy đơn giá của dịch vụ
        cursor.execute("SELECT donGia FROM tblDichVu WHERE maDV = %s", (maDV,))
        dichVu = cursor.fetchone()
        if not dichVu:
            if cursor: cursor.close()
            return jsonify({"error": f"Không tìm thấy dịch vụ với mã {maDV}"}), 404
        donGia = dichVu['donGia']
        if donGia is None: # Đảm bảo đơn giá không null
            if cursor: cursor.close()
            return jsonify({"error": f"Dịch vụ {maDV} chưa có đơn giá."}), 400

        # 2. Tính thành tiền
        thanhTien = donGia * soLuong

        # 3. Insert vào tblSuDungDichVu
        sql_insert = """
            INSERT INTO tblSuDungDichVu (maSV, maDV, thoiGianSuDung, soLuong, thanhTien)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor_insert = db_conn.cursor() # Dùng cursor thường để insert
        cursor_insert.execute(sql_insert, (maSV, maDV, thoiGianSuDung, soLuong, thanhTien))
        maSuDungMoi = cursor_insert.lastrowid
        cursor_insert.close() # Đóng cursor insert
        db_conn.commit()

        # Không cần xóa cache cụ thể nào ở đây, vì nó chỉ ảnh hưởng đến báo cáo sau này

        return jsonify({
            "message": "Ghi nhận sử dụng dịch vụ thành công",
            "maSuDung": maSuDungMoi,
            "thanhTien": thanhTien
        }), 201

    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Mã sinh viên hoặc mã dịch vụ không hợp lệ."}), 400
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi ghi nhận sử dụng dịch vụ: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close() # Đóng cursor chính (dùng để lấy đơn giá)


# Chuyển API này sang file sinh_vien.py hoặc giữ ở đây tùy cấu trúc bạn muốn
@bp.route('/sinhvien/<string:maSV>/sudung', methods=['GET'])
def get_su_dung_dich_vu_by_sv(maSV):
    """Lấy lịch sử sử dụng dịch vụ của sinh viên."""
    tuNgay = request.args.get('tuNgay')
    denNgay = request.args.get('denNgay')

    sql = """
        SELECT sdv.maSuDung, sdv.maDV, dv.tenDV, sdv.thoiGianSuDung, sdv.soLuong, sdv.thanhTien
        FROM tblSuDungDichVu sdv
        JOIN tblDichVu dv ON sdv.maDV = dv.maDV
        WHERE sdv.maSV = %s
    """
    params = [maSV]

    if tuNgay:
        sql += " AND sdv.thoiGianSuDung >= %s"
        params.append(tuNgay)
    if denNgay:
        # Lấy đến hết ngày đó
        try:
            end_date_obj = datetime.fromisoformat(denNgay).date()
            next_day = end_date_obj + timedelta(days=1)
            sql += " AND sdv.thoiGianSuDung < %s"
            params.append(next_day.isoformat())
        except ValueError:
             return jsonify({"error": "Định dạng denNgay không hợp lệ (YYYY-MM-DD)"}), 400


    sql += " ORDER BY sdv.thoiGianSuDung DESC"

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, tuple(params))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy lịch sử SDDV của SV {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()