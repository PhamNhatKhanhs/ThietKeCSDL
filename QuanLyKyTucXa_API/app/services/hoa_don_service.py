# app/services/hoa_don_service.py
from app.utils.db import get_cursor, get_db_connection
from datetime import date, datetime, timedelta
import mysql.connector

def generate_invoice_id(thangNam, maSV):
     # Tạo mã hóa đơn duy nhất, ví dụ: HD-YYYYMM-maSV
     return f"HD-{thangNam.replace('-', '')}-{maSV}"

def tao_hoa_don_cho_thang(thangNam):
    """
    Tạo hóa đơn cho tất cả sinh viên đủ điều kiện trong tháng YYYY-MM.
    Đây là một hàm phức tạp, cần xử lý cẩn thận.
    Returns:
        tuple: (success_count: int, error_list: list)
    """
    print(f"Bắt đầu tạo hóa đơn cho tháng: {thangNam}")
    success_count = 0
    error_list = []

    try:
        # 1. Xác định ngày bắt đầu, ngày kết thúc của tháng
        nam, thang = map(int, thangNam.split('-'))
        ngayDauThang = date(nam, thang, 1)
        if thang == 12:
             ngayCuoiThang = date(nam, thang, 31)
             ngayDauThangSau = date(nam + 1, 1, 1)
        else:
             ngayDauThangSau = date(nam, thang + 1, 1)
             ngayCuoiThang = ngayDauThangSau - timedelta(days=1)
        print(f"Kỳ hóa đơn: {ngayDauThang} - {ngayCuoiThang}")

    except ValueError:
         print(f"Lỗi: Định dạng tháng không hợp lệ: {thangNam}")
         error_list.append({"maSV": None, "error": "Định dạng tháng không hợp lệ"})
         return success_count, error_list

    db_conn = None
    cursor = None
    try:
        db_conn = get_db_connection()
        if not db_conn:
             raise Exception("Không thể kết nối CSDL để tạo hóa đơn")

        # Tắt auto-commit để xử lý transaction
        db_conn.autocommit = False
        cursor = db_conn.cursor(dictionary=True)

        # 2. Lấy danh sách sinh viên đang thuê phòng trong tháng đó
        cursor.execute("""
            SELECT DISTINCT hd.maSV
            FROM tblHopDongThuePhong hd
            WHERE hd.trangThai = 'Đang thuê'
              AND hd.ngayBatDau <= %s -- <= ngayCuoiThang
              AND (hd.ngayKetThuc IS NULL OR hd.ngayKetThuc >= %s) -- >= ngayDauThang
        """, (ngayCuoiThang, ngayDauThang))
        sinh_vien_list = cursor.fetchall()
        print(f"Tìm thấy {len(sinh_vien_list)} sinh viên đủ điều kiện.")

        # 3. Lặp qua từng sinh viên để tạo hóa đơn
        for sv in sinh_vien_list:
            maSV = sv['maSV']
            print(f"  Đang xử lý cho sinh viên: {maSV}")
            maHoaDon = generate_invoice_id(thangNam, maSV)

            try:
                # Kiểm tra hóa đơn đã tồn tại chưa
                cursor.execute("SELECT maHoaDon FROM tblHoaDonThanhToan WHERE maHoaDon = %s", (maHoaDon,))
                if cursor.fetchone():
                    print(f"    -> Hóa đơn {maHoaDon} đã tồn tại, bỏ qua.")
                    continue # Bỏ qua nếu đã có

                # a. Tính tiền phòng
                cursor.execute("""
                    SELECT lp.donGiaThang FROM tblHopDongThuePhong hd
                    JOIN tblPhong p ON hd.maPhong = p.maPhong
                    JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
                    WHERE hd.maSV = %s AND hd.trangThai = 'Đang thuê'
                      AND hd.ngayBatDau <= %s AND (hd.ngayKetThuc IS NULL OR hd.ngayKetThuc >= %s)
                    LIMIT 1
                """, (maSV, ngayCuoiThang, ngayDauThang))
                phong = cursor.fetchone()
                tienPhong = phong['donGiaThang'] if phong else 0

                # b. Tính tiền dịch vụ
                cursor.execute("""
                    SELECT SUM(thanhTien) as TongTienDV FROM tblSuDungDichVu
                    WHERE maSV = %s AND thoiGianSuDung >= %s AND thoiGianSuDung < %s
                """, (maSV, ngayDauThang, ngayDauThangSau))
                dichvu = cursor.fetchone()
                tienDichVu = dichvu['TongTienDV'] if dichvu and dichvu['TongTienDV'] else 0

                # c. Tính tiền gửi xe tháng
                cursor.execute("""
                    SELECT SUM(donGiaThang) as TongPhiThang FROM tblDangKyGuiXeThang
                    WHERE maSV = %s AND ngayDangKy <= %s
                      AND (ngayHetHan IS NULL OR ngayHetHan >= %s)
                """, (maSV, ngayCuoiThang, ngayDauThang))
                xe_thang = cursor.fetchone()
                tienXeThang = xe_thang['TongPhiThang'] if xe_thang and xe_thang['TongPhiThang'] else 0

                # d. Tính tiền phạt gửi xe
                cursor.execute("""
                    SELECT SUM(lgx.phiPhatSinh) AS TongPhiPhat
                    FROM tblLuotGuiLayXe lgx
                    JOIN tblDangKyGuiXeThang dgx ON lgx.maDangKy = dgx.maDangKy
                    WHERE dgx.maSV = %s AND lgx.ngay >= %s AND lgx.ngay <= %s
                 """, (maSV, ngayDauThang, ngayCuoiThang))
                xe_phat = cursor.fetchone()
                tienXePhat = xe_phat['TongPhiPhat'] if xe_phat and xe_phat['TongPhiPhat'] else 0
                tienGuiXe = tienXeThang + tienXePhat

                # e. Tính tổng cộng
                tongCong = tienPhong + tienDichVu + tienGuiXe

                # f. Insert hóa đơn
                sql_insert_hd = """
                    INSERT INTO tblHoaDonThanhToan
                    (maHoaDon, maSV, kyHoaDonTuNgay, kyHoaDonDenNgay, ngayLap,
                     tongTienPhong, tongTienDichVu, tongTienGuiXe, tongCong, trangThai)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params_hd = (
                    maHoaDon, maSV, ngayDauThang, ngayCuoiThang, datetime.now(),
                    tienPhong, tienDichVu, tienGuiXe, tongCong, 'Chưa thanh toán'
                )
                cursor_insert = db_conn.cursor() # Dùng cursor thường để insert
                cursor_insert.execute(sql_insert_hd, params_hd)
                cursor_insert.close() # Đóng cursor insert

                print(f"    -> Đã tạo hóa đơn {maHoaDon} - Tổng: {tongCong}")
                success_count += 1

            except Exception as e_sv:
                 # Lỗi khi xử lý cho 1 sinh viên cụ thể
                 print(f"    -> Lỗi khi tạo hóa đơn cho SV {maSV}: {e_sv}")
                 error_list.append({"maSV": maSV, "error": str(e_sv)})
                 db_conn.rollback() # Rollback cho sinh viên này (hoặc cho toàn bộ nếu muốn)
                 # Có thể tiếp tục với SV khác hoặc dừng lại tùy chiến lược
                 db_conn.autocommit = False # Bật lại transaction cho SV tiếp theo nếu rollback chỉ SV này


        # Kết thúc vòng lặp, commit toàn bộ nếu không có lỗi nghiêm trọng
        db_conn.commit()
        print(f"Hoàn thành tạo hóa đơn. Thành công: {success_count}, Lỗi: {len(error_list)}")

    except Exception as e_main:
        # Lỗi lớn xảy ra (ví dụ: lỗi kết nối ban đầu, lỗi query danh sách SV)
        print(f"Lỗi nghiêm trọng trong quá trình tạo hóa đơn: {e_main}")
        if db_conn: db_conn.rollback() # Rollback tất cả
        error_list.append({"maSV": None, "error": str(e_main)})
    finally:
        if db_conn: db_conn.autocommit = True # Bật lại autocommit
        if cursor: cursor.close()
        # Connection sẽ được đóng bởi teardown_appcontext

    return success_count, error_list