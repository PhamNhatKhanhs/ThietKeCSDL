# app/services/gui_xe_service.py
from app.utils.db import get_cursor
from datetime import date

def kiem_tra_gioi_han_xe(maSV):
    """
    Kiểm tra xem sinh viên đã đăng ký đủ 2 xe tháng còn hạn chưa.
    Returns:
        tuple: (allowed: bool, message: str)
    """
    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor:
            return False, "Lỗi kết nối cơ sở dữ liệu"

        # Đếm số đăng ký xe tháng còn hiệu lực (chưa hết hạn hoặc không có hạn)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tblDangKyGuiXeThang
            WHERE maSV = %s AND (ngayHetHan IS NULL OR ngayHetHan >= CURDATE())
        """, (maSV,))
        result = cursor.fetchone()
        so_xe_dang_ky = result['count'] if result else 0

        if so_xe_dang_ky >= 2:
            return False, "Sinh viên đã đăng ký đủ 2 xe tháng."
        else:
            return True, f"Sinh viên còn có thể đăng ký {2 - so_xe_dang_ky} xe."

    except Exception as e:
        print(f"Lỗi kiểm tra giới hạn xe cho SV {maSV}: {e}")
        return False, "Lỗi máy chủ khi kiểm tra giới hạn xe"
    finally:
        if cursor:
            cursor.close()


def tinh_phi_phat_sinh(maDangKy, ngay):
    """
    Tính phí phát sinh cho lượt gửi/lấy xe dựa vào số lượt đã có trong ngày.
    Args:
        maDangKy (str): Mã đăng ký xe tháng.
        ngay (date | str): Ngày cần kiểm tra (đối tượng date hoặc chuỗi YYYY-MM-DD).
    Returns:
        int: 0 (miễn phí), 3000 (phí phát sinh), hoặc -1 (lỗi).
    """
    if isinstance(ngay, str):
        try:
            ngay_dt = date.fromisoformat(ngay)
        except ValueError:
            print(f"Định dạng ngày không hợp lệ: {ngay}")
            return -1 # Lỗi định dạng ngày
    elif isinstance(ngay, date):
        ngay_dt = ngay
    else:
        print(f"Kiểu dữ liệu ngày không hợp lệ: {type(ngay)}")
        return -1

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor:
            return -1 # Lỗi kết nối

        # Đếm số lượt đã vào hoặc ra trong ngày
        # Lưu ý: Cần làm rõ logic đếm. Ví dụ: 1 lần vào + 1 lần ra = 2 lượt? Hay 1 cặp vào/ra = 1 lượt?
        # Giả sử mỗi bản ghi trong tblLuotGuiLayXe là 1 "lượt" sử dụng cổng.
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tblLuotGuiLayXe
            WHERE maDangKy = %s AND ngay = %s
        """, (maDangKy, ngay_dt))
        result = cursor.fetchone()
        so_luot_da_thuc_hien = result['count'] if result else 0

        # Giới hạn miễn phí là 2 lượt (ví dụ: 1 lần vào và 1 lần ra)
        # Lượt thứ 3 trở đi sẽ tính phí
        if so_luot_da_thuc_hien >= 2:
            return 3000 # Phí phát sinh
        else:
            return 0 # Miễn phí

    except Exception as e:
        print(f"Lỗi tính phí phát sinh cho {maDangKy} ngày {ngay_dt}: {e}")
        return -1 # Lỗi tính toán
    finally:
        if cursor:
            cursor.close()

# Thêm các hàm service khác liên quan đến gửi xe nếu cần