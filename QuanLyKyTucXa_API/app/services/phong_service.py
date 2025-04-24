# app/services/phong_service.py
from app.utils.db import get_cursor
from flask import current_app # Import current_app nếu cần truy cập config

def kiem_tra_phong_trong(maPhong):
    """
    Kiểm tra xem phòng còn chỗ trống không và trả về sức chứa.
    Returns:
        tuple: (is_available: bool, message: str, suc_chua: int | None)
               Ví dụ: (True, "Phòng còn chỗ", 4)
                      (False, "Phòng đã đủ người", 4)
                      (False, "Không tìm thấy phòng hoặc loại phòng", None)
    """
    cursor = None
    suc_chua = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor:
            # Không log lỗi ở đây vì get_cursor đã log rồi
            return False, "Lỗi kết nối cơ sở dữ liệu", None

        # Lấy sức chứa của phòng
        cursor.execute("""
            SELECT lp.sucChua
            FROM tblPhong p
            JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
            WHERE p.maPhong = %s
        """, (maPhong,))
        phong_info = cursor.fetchone()

        if not phong_info:
            return False, f"Không tìm thấy phòng với mã {maPhong}", None

        suc_chua = phong_info['sucChua']

        # Đếm số hợp đồng đang thuê trong phòng đó
        cursor.execute("""
            SELECT COUNT(*) as soNguoiHienTai
            FROM tblHopDongThuePhong
            WHERE maPhong = %s AND trangThai = 'Đang thuê'
        """, (maPhong,))
        hop_dong_info = cursor.fetchone()
        so_nguoi_hien_tai = hop_dong_info['soNguoiHienTai'] if hop_dong_info else 0

        if so_nguoi_hien_tai < suc_chua:
            return True, f"Phòng còn {suc_chua - so_nguoi_hien_tai} chỗ trống", suc_chua
        else:
            return False, "Phòng đã đủ người", suc_chua

    except Exception as e:
        print(f"Lỗi khi kiểm tra phòng trống {maPhong}: {e}")
        return False, "Lỗi máy chủ khi kiểm tra phòng", None
    finally:
        if cursor:
            cursor.close()

# Thêm các hàm service khác liên quan đến phòng nếu cần
# Ví dụ: hàm lấy danh sách phòng trống theo loại phòng...