# app/routes/hoa_don.py
from flask import Blueprint, jsonify, request
from app.utils.db import get_cursor, get_db_connection
from app.utils.cache import get_cache, set_cache, delete_cache, delete_cache_pattern
import mysql.connector
from datetime import datetime
# Import service tạo hóa đơn
from app.services.hoa_don_service import tao_hoa_don_cho_thang

bp = Blueprint('hoa_don', __name__, url_prefix='/api/hoadon')

@bp.route('/', methods=['GET'])
def get_all_hoa_don():
    """Lấy danh sách hóa đơn (có thể lọc theo sinh viên, kỳ)."""
    maSV = request.args.get('maSV')
    tuNgay = request.args.get('tuNgay') # Filter theo ngày bắt đầu kỳ hóa đơn
    denNgay = request.args.get('denNgay') # Filter theo ngày kết thúc kỳ hóa đơn
    trangThai = request.args.get('trangThai') # Filter theo trạng thái

    # Lấy danh sách hóa đơn (có thể thêm phân trang)
    sql = """
        SELECT hd.*, sv.hoTen AS tenSinhVien
        FROM tblHoaDonThanhToan hd
        JOIN tblSinhVien sv ON hd.maSV = sv.maSV
        WHERE 1=1
    """
    params = []
    if maSV:
        sql += " AND hd.maSV = %s"
        params.append(maSV)
    if tuNgay:
        sql += " AND hd.kyHoaDonTuNgay >= %s"
        params.append(tuNgay)
    if denNgay:
        sql += " AND hd.kyHoaDonDenNgay <= %s"
        params.append(denNgay)
    if trangThai:
         sql += " AND hd.trangThai = %s"
         params.append(trangThai)

    sql += " ORDER BY hd.ngayLap DESC"

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute(sql, tuple(params))
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        print(f"Lỗi lấy danh sách hóa đơn: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


@bp.route('/<string:maHoaDon>', methods=['GET'])
def get_hoa_don_by_id(maHoaDon):
    """Lấy chi tiết hóa đơn."""
    cache_key = f"hoadon:{maHoaDon}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500
        cursor.execute("""
             SELECT hd.*, sv.hoTen AS tenSinhVien
             FROM tblHoaDonThanhToan hd
             JOIN tblSinhVien sv ON hd.maSV = sv.maSV
             WHERE hd.maHoaDon = %s
        """, (maHoaDon,))
        result = cursor.fetchone()
        if result:
             set_cache(cache_key, result)
             return jsonify(result)
        else:
             return jsonify({"message": "Không tìm thấy hóa đơn"}), 404
    except Exception as e:
        print(f"Lỗi lấy chi tiết hóa đơn {maHoaDon}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        if cursor: cursor.close()


@bp.route('/<string:maHoaDon>/thanh-toan', methods=['PUT'])
def update_trang_thai_thanh_toan(maHoaDon):
    """Đánh dấu hóa đơn đã thanh toán."""
    ngayThanhToan = datetime.now()

    sql = "UPDATE tblHoaDonThanhToan SET trangThai = 'Đã thanh toán', ngayThanhToan = %s WHERE maHoaDon = %s AND trangThai = 'Chưa thanh toán'"

    cursor = None
    db_conn = None
    try:
        db_conn = get_db_connection()
        cursor_check = db_conn.cursor(dictionary=True) # Cursor để kiểm tra trước
        cursor_update = db_conn.cursor() # Cursor để cập nhật

        if not cursor_check or not cursor_update: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # Kiểm tra hóa đơn tồn tại và trạng thái
        cursor_check.execute("SELECT trangThai FROM tblHoaDonThanhToan WHERE maHoaDon = %s", (maHoaDon,))
        hd = cursor_check.fetchone()
        if not hd:
            return jsonify({"message": f"Không tìm thấy hóa đơn {maHoaDon}"}), 404
        elif hd['trangThai'] == 'Đã thanh toán':
            return jsonify({"message": f"Hóa đơn {maHoaDon} đã được thanh toán trước đó"}), 400

        # Thực hiện cập nhật
        cursor_update.execute(sql, (ngayThanhToan, maHoaDon))

        db_conn.commit()

        # Xóa cache của hóa đơn này
        delete_cache(f"hoadon:{maHoaDon}")

        return jsonify({"message": f"Đã cập nhật thanh toán cho hóa đơn {maHoaDon}"}), 200
    except Exception as e:
        if db_conn: db_conn.rollback()
        print(f"Lỗi cập nhật thanh toán hóa đơn {maHoaDon}: {e}")
        return jsonify({"error": "Lỗi máy chủ"}), 500
    finally:
        # Đóng cả hai cursor nếu chúng được tạo
        if 'cursor_check' in locals() and cursor_check: cursor_check.close()
        if 'cursor_update' in locals() and cursor_update: cursor_update.close()


@bp.route('/tao', methods=['POST'])
def generate_monthly_invoices_api():
    """API để kích hoạt việc tạo hóa đơn cho một tháng cụ thể."""
    data = request.get_json()
    thangNam = data.get('thang') # Ví dụ: "2025-04"
    if not thangNam:
        return jsonify({"error": "Thiếu tham số 'thang' (YYYY-MM)"}), 400

    # Gọi hàm service để thực hiện logic tạo hóa đơn
    try:
         success_count, error_list = tao_hoa_don_cho_thang(thangNam) # Gọi service
         if error_list:
             # Trả về thông tin lỗi nếu có
             return jsonify({
                 "message": f"Quá trình tạo hóa đơn tháng {thangNam} hoàn tất với một số lỗi.",
                 "created_count": success_count,
                 "errors": error_list
             }), 207 # Multi-Status
         elif success_count > 0:
              return jsonify({
                 "message": f"Đã tạo thành công {success_count} hóa đơn cho tháng {thangNam}."
             }), 201 # Created (hoặc 200 OK)
         else:
              return jsonify({
                  "message": f"Không có hóa đơn nào cần tạo cho tháng {thangNam} (có thể đã tạo trước đó hoặc không có SV đủ điều kiện)."
              }), 200 # OK

    except Exception as e:
         print(f"Lỗi khi gọi service tạo hóa đơn tháng {thangNam}: {e}")
         return jsonify({"error": "Lỗi máy chủ khi kích hoạt tạo hóa đơn"}), 500