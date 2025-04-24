# app/routes/gui_xe.py
from flask import Blueprint, jsonify, request
from app.utils.db import get_cursor, get_db_connection
from app.utils.cache import delete_cache # Chỉ cần xóa cache nếu có
import mysql.connector
from datetime import datetime, date # Import date
# Import các service cần thiết
from app.services.gui_xe_service import kiem_tra_gioi_han_xe, tinh_phi_phat_sinh

bp = Blueprint('gui_xe', __name__, url_prefix='/api/guixe')

# --- API cho Xe ---
@bp.route('/xe', methods=['POST'])
def create_xe():
    """Thêm xe mới cho sinh viên."""
    data = request.get_json()
    if not data or not data.get('bienSoXe') or not data.get('maSV'):
        return jsonify({"error": "Thiếu thông tin bắt buộc (bienSoXe, maSV)"}), 400

    sql = "INSERT INTO tblXe (bienSoXe, maSV, loaiXe, mauSac, ghiChu) VALUES (%s, %s, %s, %s, %s)"
    params = (data['bienSoXe'], data['maSV'], data.get('loaiXe'), data.get('mauSac'), data.get('ghiChu'))

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, params)
        db_conn.commit()
        # Có thể xóa cache liên quan đến danh sách xe của SV nếu có
        return jsonify({"message": "Thêm xe thành công", "xe": data}), 201
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        err_msg = str(e)
        field = "Biển số xe" if "PRIMARY" in err_msg else "Mã sinh viên" if "maSV" in err_msg else "Khóa"
        return jsonify({"error": f"{field} đã tồn tại hoặc không hợp lệ."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi thêm xe: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/sinhvien/<string:maSV>/xe', methods=['GET'])
def get_xe_by_sv(maSV):
    """Lấy danh sách xe của sinh viên."""
    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("SELECT * FROM tblXe WHERE maSV = %s", (maSV,))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách xe của SV {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/xe/<path:bienSoXe>', methods=['PUT']) # Dùng path vì biển số có thể chứa ký tự đặc biệt? Hoặc string là đủ.
def update_xe(bienSoXe):
    """Cập nhật thông tin xe."""
    data = request.get_json()
    if not data: return jsonify({"error": "Không có dữ liệu cập nhật"}), 400

    set_clauses = []
    params = []
    allowed_fields = ['maSV', 'loaiXe', 'mauSac', 'ghiChu'] # Không cho sửa biển số
    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses: return jsonify({"error": "Không có trường hợp lệ để cập nhật"}), 400

    params.append(bienSoXe)
    query = f"UPDATE tblXe SET {', '.join(set_clauses)} WHERE bienSoXe = %s"
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(query, tuple(params))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy xe {bienSoXe}"}), 404
        db_conn.commit()
        # Xóa cache liên quan nếu có
        return jsonify({"message": f"Cập nhật xe {bienSoXe} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Mã sinh viên không hợp lệ."}), 400
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật xe {bienSoXe}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


@bp.route('/xe/<path:bienSoXe>', methods=['DELETE'])
def delete_xe(bienSoXe):
    """Xóa một xe."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("DELETE FROM tblXe WHERE bienSoXe = %s", (bienSoXe,))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy xe {bienSoXe}"}), 404
        db_conn.commit()
        # Xóa cache liên quan nếu có
        return jsonify({"message": f"Xóa xe {bienSoXe} thành công"}), 200
    except mysql.connector.IntegrityError as e:
        # Lỗi nếu còn đăng ký gửi xe tháng liên kết
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Không thể xóa xe vì còn đăng ký gửi xe tháng"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa xe {bienSoXe}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


# --- API cho Đăng ký Gửi xe Tháng ---
@bp.route('/dangky', methods=['POST'])
def add_dang_ky_gui_xe():
    """Đăng ký gửi xe tháng cho sinh viên."""
    data = request.get_json()
    required_fields = ['maDangKy', 'maSV', 'bienSoXe', 'ngayDangKy']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": f"Thiếu thông tin bắt buộc ({', '.join(required_fields)})"}), 400

    maSV = data['maSV']

    # 1. Gọi Service Kiểm tra Giới hạn Xe
    allowed, message = kiem_tra_gioi_han_xe(maSV)
    if not allowed:
        return jsonify({"error": message}), 409 # 409 Conflict

    # 2. Insert vào DB
    sql = """
        INSERT INTO tblDangKyGuiXeThang
        (maDangKy, maSV, bienSoXe, ngayDangKy, ngayHetHan, donGiaThang)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        data['maDangKy'], maSV, data['bienSoXe'], data['ngayDangKy'],
        data.get('ngayHetHan'), data.get('donGiaThang', 100000) # Lấy giá mặc định
    )

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        cursor.execute(sql, params)
        db_conn.commit()
        return jsonify({"message": "Đăng ký gửi xe thành công", "dangKy": data}), 201
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        err_msg = str(e)
        field = "Mã đăng ký" if "PRIMARY" in err_msg else "Mã SV hoặc Biển số xe" if "FOREIGN KEY" in err_msg else "Khóa"
        return jsonify({"error": f"{field} đã tồn tại hoặc không hợp lệ."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi đăng ký gửi xe: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/sinhvien/<string:maSV>/dangky', methods=['GET'])
def get_dang_ky_by_sv(maSV):
    """Lấy danh sách đăng ký gửi xe của sinh viên."""
    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("""
            SELECT d.*, x.loaiXe, x.mauSac
            FROM tblDangKyGuiXeThang d
            JOIN tblXe x ON d.bienSoXe = x.bienSoXe
            WHERE d.maSV = %s
            ORDER BY d.ngayDangKy DESC
        """, (maSV,))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách đăng ký xe của SV {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/dangky/<string:maDangKy>', methods=['PUT'])
def update_dang_ky_gui_xe(maDangKy):
    """Cập nhật đăng ký xe (ví dụ: gia hạn)."""
    data = request.get_json()
    if not data or 'ngayHetHan' not in data: # Chỉ cho phép cập nhật ngày hết hạn?
        return jsonify({"error": "Chỉ có thể cập nhật ngayHetHan"}), 400

    ngayHetHan = data['ngayHetHan']

    sql = "UPDATE tblDangKyGuiXeThang SET ngayHetHan = %s WHERE maDangKy = %s"
    params = (ngayHetHan, maDangKy)

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, params)
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy đăng ký {maDangKy}"}), 404
        db_conn.commit()
        # Xóa cache liên quan nếu có
        return jsonify({"message": f"Cập nhật đăng ký {maDangKy} thành công"}), 200
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật đăng ký xe {maDangKy}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/dangky/<string:maDangKy>', methods=['DELETE'])
def delete_dang_ky_gui_xe(maDangKy):
    """Xóa một đăng ký gửi xe."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("DELETE FROM tblDangKyGuiXeThang WHERE maDangKy = %s", (maDangKy,))
        if cursor.rowcount == 0: return jsonify({"message": f"Không tìm thấy đăng ký {maDangKy}"}), 404
        db_conn.commit()
        # Xóa cache liên quan nếu có
        # Lưu ý: Xóa đăng ký có thể ảnh hưởng đến các lượt gửi xe đã ghi nhận? Cần xem xét FK constraint
        return jsonify({"message": f"Xóa đăng ký {maDangKy} thành công"}), 200
    except mysql.connector.IntegrityError as e:
         # Lỗi nếu còn lượt gửi xe liên kết (FK nên là ON DELETE CASCADE trong tblLuotGuiLayXe thì sẽ không lỗi)
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Không thể xóa đăng ký vì còn lượt gửi/lấy xe liên quan"}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi xóa đăng ký xe {maDangKy}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

# --- API cho Lượt Gửi/Lấy Xe ---
@bp.route('/luot', methods=['POST'])
def add_luot_gui_lay_xe():
    """Ghi nhận một lượt gửi hoặc lấy xe."""
    data = request.get_json()
    if not data or not data.get('maDangKy'):
        return jsonify({"error": "Thiếu mã đăng ký (maDangKy)"}), 400

    maDangKy = data['maDangKy']
    ngay_str = data.get('ngay', date.today().isoformat())
    try:
        ngay_dt = date.fromisoformat(ngay_str)
    except ValueError:
        return jsonify({"error": "Định dạng ngày không hợp lệ (YYYY-MM-DD)"}), 400

    thoiGianVao = data.get('thoiGianVao')
    thoiGianRa = data.get('thoiGianRa')

    # 1. Gọi Service tính phí phát sinh
    phi_phat = tinh_phi_phat_sinh(maDangKy, ngay_dt)
    if phi_phat < 0: # Lỗi khi tính
         return jsonify({"error": "Lỗi khi tính phí phát sinh (kiểm tra service log)"}), 500

    # 2. Insert vào DB
    sql = """
        INSERT INTO tblLuotGuiLayXe (maDangKy, ngay, thoiGianVao, thoiGianRa, phiPhatSinh)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (maDangKy, ngay_dt, thoiGianVao, thoiGianRa, phi_phat)

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        cursor.execute(sql, params)
        maLuotMoi = cursor.lastrowid
        db_conn.commit()
        return jsonify({
            "message": "Ghi nhận lượt gửi/lấy xe thành công",
            "maLuot": maLuotMoi,
            "phiPhatSinh": phi_phat
        }), 201
    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        return jsonify({"error": "Mã đăng ký không hợp lệ."}), 400
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi ghi nhận lượt gửi/lấy xe: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()

@bp.route('/dangky/<string:maDangKy>/luot', methods=['GET'])
def get_luot_xe_by_dang_ky(maDangKy):
    """Lấy lịch sử gửi/lấy xe của một đăng ký."""
    ngay = request.args.get('ngay') # Filter theo ngày nếu có

    sql = "SELECT * FROM tblLuotGuiLayXe WHERE maDangKy = %s"
    params = [maDangKy]
    if ngay:
        sql += " AND ngay = %s"
        params.append(ngay)
    sql += " ORDER BY ngay DESC, thoiGianVao DESC, thoiGianRa DESC" # Sắp xếp hợp lý hơn

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, tuple(params))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy lượt xe của đăng ký {maDangKy}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()