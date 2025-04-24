# app/routes/sinh_vien.py
from flask import Blueprint, jsonify, request
from app.utils.db import get_cursor, get_db_connection # Import thêm get_db_connection để commit/rollback
from app.utils.cache import get_cache, set_cache, delete_cache, delete_cache_pattern # Import thêm delete_cache_pattern nếu muốn xóa theo mẫu
import mysql.connector # Import để bắt lỗi cụ thể của MySQL

# Tạo Blueprint cho Sinh Viên
bp = Blueprint('sinh_vien', __name__, url_prefix='/api/sinhvien')

# --- API Lấy danh sách Sinh Viên ---
@bp.route('/', methods=['GET'])
def get_all_sinh_vien():
    """Lấy danh sách tất cả sinh viên."""
    # 1. Kiểm tra Cache
    cache_key = "sinhvien:list"
    cached_data = get_cache(cache_key)
    if cached_data:
        # print(f"Cache hit for {cache_key}") # Bỏ comment nếu muốn debug cache
        return jsonify(cached_data)

    # print(f"Cache miss for {cache_key}") # Bỏ comment nếu muốn debug cache
    # 2. Query Database
    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor:
            return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

        print(f"Executing DB query for key: {cache_key}") # Log để biết khi nào query DB
        cursor.execute("SELECT maSV, hoTen, soCMT, ngaySinh, lop, queQuan FROM tblSinhVien ORDER BY maSV")
        sinhvien_list = cursor.fetchall() # Lấy tất cả các dòng

        # 3. Lưu vào Cache (hàm set_cache đã xử lý date/datetime)
        set_cache(cache_key, sinhvien_list)

        return jsonify(sinhvien_list)

    except Exception as e:
        print(f"Lỗi khi truy vấn danh sách sinh viên: {e}")
        return jsonify({"error": "Lỗi máy chủ nội bộ khi truy vấn dữ liệu"}), 500
    finally:
        if cursor:
            cursor.close()

# --- API Lấy chi tiết Sinh Viên ---
@bp.route('/<string:maSV>', methods=['GET'])
def get_sinh_vien_by_id(maSV):
    """Lấy thông tin chi tiết của một sinh viên."""
    if not maSV:
        return jsonify({"error": "Thiếu mã sinh viên"}), 400

    # 1. Kiểm tra Cache trước
    cache_key = f"sinhvien:{maSV}"
    cached_data = get_cache(cache_key)
    if cached_data:
        # print(f"Cache hit for {cache_key}")
        return jsonify(cached_data)

    # print(f"Cache miss for {cache_key}")
    # 2. Nếu không có cache, query Database
    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor:
            return jsonify({"error": "Không thể kết nối đến cơ sở dữ liệu"}), 500

        print(f"Executing DB query for key: {cache_key}")
        cursor.execute("""
            SELECT maSV, hoTen, soCMT, ngaySinh, lop, queQuan
            FROM tblSinhVien
            WHERE maSV = %s
        """, (maSV,))
        sinhvien = cursor.fetchone()

        if sinhvien:
            # 3. Lưu kết quả vào Cache
            set_cache(cache_key, sinhvien)
            return jsonify(sinhvien)
        else:
            return jsonify({"message": "Không tìm thấy sinh viên"}), 404

    except Exception as e:
        print(f"Lỗi khi truy vấn sinh viên {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ nội bộ khi truy vấn dữ liệu"}), 500
    finally:
        if cursor:
            cursor.close()

# --- API Tạo mới Sinh Viên ---
@bp.route('/', methods=['POST'])
def create_sinh_vien():
    """Tạo một sinh viên mới."""
    data = request.get_json()

    # 1. Validate dữ liệu đầu vào
    if not data or not data.get('maSV') or not data.get('hoTen') or not data.get('soCMT'):
        return jsonify({"error": "Thiếu thông tin bắt buộc (maSV, hoTen, soCMT)"}), 400

    maSV = data['maSV']
    hoTen = data['hoTen']
    soCMT = data['soCMT']
    ngaySinh = data.get('ngaySinh') # Có thể None
    lop = data.get('lop')         # Có thể None
    queQuan = data.get('queQuan') # Có thể None

    # (Thêm các bước validate chi tiết hơn nếu cần: định dạng ngày, độ dài mã SV...)

    # 2. Insert vào Database
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection() # Lấy connection để commit/rollback
        cursor = db_conn.cursor()
        if not cursor:
            return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

        cursor.execute("""
            INSERT INTO tblSinhVien (maSV, hoTen, soCMT, ngaySinh, lop, queQuan)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (maSV, hoTen, soCMT, ngaySinh, lop, queQuan))

        db_conn.commit() # Lưu thay đổi vào DB

        # 3. Xóa cache danh sách (vì danh sách đã thay đổi)
        delete_cache("sinhvien:list")

        # 4. Trả về thông tin sinh viên vừa tạo (tùy chọn)
        # Có thể query lại hoặc trả về chính data đã gửi đi
        return jsonify({
            "message": "Tạo sinh viên thành công",
            "sinhVien": {
                "maSV": maSV,
                "hoTen": hoTen,
                "soCMT": soCMT,
                "ngaySinh": ngaySinh,
                "lop": lop,
                "queQuan": queQuan
            }
        }), 201 # 201 Created

    except mysql.connector.IntegrityError as e:
         # Bắt lỗi nếu vi phạm ràng buộc UNIQUE (maSV hoặc soCMT đã tồn tại)
        if db_conn: db_conn.rollback()
        error_code, error_message = e.args
        print(f"Lỗi UNIQUE khi tạo sinh viên: {error_message}")
        field = "Mã sinh viên" if "maSV" in error_message else "Số CMT" if "soCMT" in error_message else "Trường UNIQUE khác"
        return jsonify({"error": f"{field} đã tồn tại."}), 409 # 409 Conflict
    except Exception as e:
        if db_conn: db_conn.rollback() # Rollback nếu có lỗi khác
        print(f"Lỗi khi tạo sinh viên: {e}")
        return jsonify({"error": "Lỗi máy chủ nội bộ khi tạo sinh viên"}), 500
    finally:
        if cursor:
            cursor.close()

# --- API Cập nhật Sinh Viên ---
@bp.route('/<string:maSV>', methods=['PUT'])
def update_sinh_vien(maSV):
    """Cập nhật thông tin sinh viên."""
    data = request.get_json()

    # 1. Validate dữ liệu
    if not data:
        return jsonify({"error": "Không có dữ liệu để cập nhật"}), 400

    # 2. Xây dựng câu lệnh UPDATE động
    set_clauses = []
    params = []
    allowed_fields = ['hoTen', 'soCMT', 'ngaySinh', 'lop', 'queQuan'] # Các trường cho phép cập nhật

    for field in allowed_fields:
        if field in data:
            set_clauses.append(f"{field} = %s")
            params.append(data[field])

    if not set_clauses:
        return jsonify({"error": "Không có trường hợp lệ nào để cập nhật"}), 400

    params.append(maSV) # Thêm maSV vào cuối cho mệnh đề WHERE

    # 3. Thực thi UPDATE
    query = f"UPDATE tblSinhVien SET {', '.join(set_clauses)} WHERE maSV = %s"
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor:
            return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

        cursor.execute(query, tuple(params))

        if cursor.rowcount == 0:
             # Không có dòng nào được cập nhật -> Mã SV không tồn tại
            return jsonify({"message": f"Không tìm thấy sinh viên với mã {maSV}"}), 404

        db_conn.commit() # Lưu thay đổi

        # 4. Xóa cache liên quan
        delete_cache(f"sinhvien:{maSV}")
        delete_cache("sinhvien:list") # Xóa cả cache danh sách

        return jsonify({"message": f"Cập nhật sinh viên {maSV} thành công"}), 200

    except mysql.connector.IntegrityError as e:
        if db_conn: db_conn.rollback()
        error_code, error_message = e.args
        print(f"Lỗi UNIQUE khi cập nhật sinh viên: {error_message}")
        field = "Số CMT" if "soCMT" in error_message else "Trường UNIQUE khác"
        return jsonify({"error": f"{field} đã tồn tại."}), 409
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi khi cập nhật sinh viên {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ nội bộ khi cập nhật sinh viên"}), 500
    finally:
        if cursor:
            cursor.close()

# --- API Xóa Sinh Viên ---
@bp.route('/<string:maSV>', methods=['DELETE'])
def delete_sinh_vien(maSV):
    """Xóa một sinh viên."""
    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        if not cursor:
            return jsonify({"error": "Lỗi kết nối cơ sở dữ liệu"}), 500

        cursor.execute("DELETE FROM tblSinhVien WHERE maSV = %s", (maSV,))

        if cursor.rowcount == 0:
            return jsonify({"message": f"Không tìm thấy sinh viên với mã {maSV}"}), 404

        db_conn.commit() # Lưu thay đổi

        # Xóa cache liên quan
        delete_cache(f"sinhvien:{maSV}")
        delete_cache("sinhvien:list")

        return jsonify({"message": f"Xóa sinh viên {maSV} thành công"}), 200 # Hoặc 204 No Content

    except mysql.connector.IntegrityError as e:
        # Thường xảy ra nếu có Foreign Key ON DELETE RESTRICT ở bảng khác trỏ tới SinhVien
        if db_conn: db_conn.rollback()
        print(f"Lỗi FK khi xóa sinh viên {maSV}: {e}")
        return jsonify({"error": "Không thể xóa sinh viên do còn dữ liệu liên quan (hợp đồng, đăng ký xe,...)"}), 409 # 409 Conflict
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi khi xóa sinh viên {maSV}: {e}")
        return jsonify({"error": "Lỗi máy chủ nội bộ khi xóa sinh viên"}), 500
    finally:
        if cursor:
            cursor.close()