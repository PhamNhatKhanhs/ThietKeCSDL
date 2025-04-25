# app/routes/bao_cao.py
from flask import Blueprint, jsonify, request
from app.utils.db import get_cursor
from app.utils.cache import get_cache, set_cache # Có thể cache báo cáo
from datetime import datetime, date, timedelta

bp = Blueprint('bao_cao', __name__, url_prefix='/api/bao-cao')

# --- API Báo cáo 1: Chi phí sinh viên hàng tháng ---
@bp.route('/chi-phi-sinh-vien', methods=['GET'])
def report_chi_phi_sinh_vien():
    thangXem = request.args.get('thang') # YYYY-MM
    maSV_filter = request.args.get('maSV')

    if not thangXem:
        return jsonify({"error": "Thiếu tham số 'thang' (YYYY-MM)"}), 400

    # Cố gắng chuẩn hóa định dạng tháng thành YYYY-MM
    try:
        if len(thangXem.split('-')[1]) == 1: # Nếu tháng chỉ có 1 chữ số (ví dụ 2025-4)
            thangXem = thangXem.split('-')[0] + '-0' + thangXem.split('-')[1] # Chuyển thành 2025-04
        # Xác định ngày đầu và cuối tháng
        namXem = int(thangXem.split('-')[0])
        thangXem_INT = int(thangXem.split('-')[1])
        if not (1 <= thangXem_INT <= 12): raise ValueError("Tháng không hợp lệ")
        ngayDauThang = date(namXem, thangXem_INT, 1)
        if thangXem_INT == 12:
             ngayCuoiThang = date(namXem, thangXem_INT, 31)
        else:
             ngayCuoiThang = date(namXem, thangXem_INT + 1, 1) - timedelta(days=1)
        # Tính ngày đầu tháng sau cho truy vấn dịch vụ
        if thangXem_INT == 12:
            ngayDauThangSau = date(namXem + 1, 1, 1)
        else:
            ngayDauThangSau = date(namXem, thangXem_INT + 1, 1)

    except (ValueError, IndexError):
         return jsonify({"error": "Định dạng tháng không hợp lệ (cần YYYY-MM, ví dụ 2025-04)"}), 400

    cache_key = f"report:chiphi:{thangXem}"
    if maSV_filter:
        cache_key += f":{maSV_filter}"

    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        sql = """
            SELECT
                sv.maSV,
                sv.hoTen,
                %s AS ThangNam,
                IFNULL(tp.GiaThang, 0) AS TienPhong, -- Đổi tên alias cho rõ
                IFNULL(tdv.TongTienDV, 0) AS TienDichVu,
                IFNULL(tgx_thang.TongPhiThang, 0) AS TienGuiXe_PhiThang,
                IFNULL(tgx_phat.TongPhiPhat, 0) AS TienGuiXe_Phat,
                (IFNULL(tp.GiaThang, 0) +
                 IFNULL(tdv.TongTienDV, 0) +
                 IFNULL(tgx_thang.TongPhiThang, 0) +
                 IFNULL(tgx_phat.TongPhiPhat, 0)
                ) AS TongCongThang
            FROM
                tblSinhVien sv
            LEFT JOIN (
                -- SỬA Ở ĐÂY: Dùng MAX() hoặc MIN() cho donGiaThang
                SELECT hd.maSV, MAX(lp.donGiaThang) AS GiaThang
                FROM tblHopDongThuePhong hd
                JOIN tblPhong p ON hd.maPhong = p.maPhong
                JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
                WHERE hd.trangThai = 'Đang thuê'
                  AND hd.ngayBatDau <= %s -- ngayCuoiThang
                  AND (hd.ngayKetThuc IS NULL OR hd.ngayKetThuc >= %s) -- ngayDauThang
                GROUP BY hd.maSV -- Chỉ cần group by maSV là đủ khi đã dùng MAX()
            ) tp ON sv.maSV = tp.maSV
            LEFT JOIN (
                SELECT maSV, SUM(thanhTien) AS TongTienDV
                FROM tblSuDungDichVu
                WHERE thoiGianSuDung >= %s AND thoiGianSuDung < %s -- Dùng ngayDauThangSau
                GROUP BY maSV
            ) tdv ON sv.maSV = tdv.maSV
            LEFT JOIN (
                SELECT maSV, SUM(donGiaThang) AS TongPhiThang
                FROM tblDangKyGuiXeThang
                WHERE ngayDangKy <= %s -- ngayCuoiThang
                  AND (ngayHetHan IS NULL OR ngayHetHan >= %s) -- ngayDauThang
                GROUP BY maSV
            ) tgx_thang ON sv.maSV = tgx_thang.maSV
            LEFT JOIN (
                 SELECT dgx.maSV, SUM(lgx.phiPhatSinh) AS TongPhiPhat
                 FROM tblLuotGuiLayXe lgx
                 JOIN tblDangKyGuiXeThang dgx ON lgx.maDangKy = dgx.maDangKy
                 WHERE lgx.ngay >= %s AND lgx.ngay <= %s -- ngayDauThang, ngayCuoiThang
                 GROUP BY dgx.maSV
            ) tgx_phat ON sv.maSV = tgx_phat.maSV
            WHERE 1=1
        """
        # Sửa lại thứ tự và giá trị params cho đúng với query mới
        params = [
            thangXem,              # Cho %s AS ThangNam
            ngayCuoiThang,         # Cho tiền phòng (ngayBatDau <=)
            ngayDauThang,          # Cho tiền phòng (ngayKetThuc >=)
            ngayDauThang,         # Cho tiền dịch vụ (thoiGianSuDung >=)
            ngayDauThangSau,       # Cho tiền dịch vụ (thoiGianSuDung <) -> Sửa lại param này
            ngayCuoiThang,         # Cho phí xe tháng (ngayDangKy <=)
            ngayDauThang,          # Cho phí xe tháng (ngayHetHan >=)
            ngayDauThang,         # Cho phí phạt (lgx.ngay >=)
            ngayCuoiThang         # Cho phí phạt (lgx.ngay <=)
        ]

        if maSV_filter:
            sql += " AND sv.maSV = %s"
            params.append(maSV_filter)

        sql += " ORDER BY sv.maSV"

        cursor.execute(sql, tuple(params)) # Đảm bảo params là tuple
        result = cursor.fetchall()

        set_cache(cache_key, result)
        return jsonify(result)

    except Exception as e:
        print(f"Lỗi báo cáo chi phí sinh viên tháng {thangXem}: {e}")
        # In query và params nếu cần debug
        # print("SQL:", sql)
        # print("Params:", tuple(params))
        return jsonify({"error": "Lỗi máy chủ khi tạo báo cáo"}), 500
    finally:
        if cursor: cursor.close()



# --- API Báo cáo 2: Dịch vụ sinh viên sử dụng ---
@bp.route('/su-dung-dich-vu', methods=['GET'])
def report_su_dung_dich_vu():
    tuNgay = request.args.get('tuNgay') # YYYY-MM-DD
    denNgay = request.args.get('denNgay') # YYYY-MM-DD
    maSV_filter = request.args.get('maSV') # Tùy chọn

    if not tuNgay or not denNgay:
         return jsonify({"error": "Thiếu tham số 'tuNgay' hoặc 'denNgay' (YYYY-MM-DD)"}), 400

    # Thêm validation định dạng ngày nếu cần

    cache_key = f"report:sddv:{tuNgay}:{denNgay}"
    if maSV_filter: cache_key += f":{maSV_filter}"

    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # Query 2
        sql = """
            SELECT
                sv.maSV,
                sv.hoTen,
                dv.tenDV,
                SUM(sdv.thanhTien) AS TongGiaDichVu
            FROM
                tblSinhVien sv
            JOIN tblSuDungDichVu sdv ON sv.maSV = sdv.maSV
            JOIN tblDichVu dv ON sdv.maDV = dv.maDV
            WHERE
                sdv.thoiGianSuDung >= %s
                AND sdv.thoiGianSuDung < DATE_ADD(%s, INTERVAL 1 DAY)
        """
        params = [tuNgay, denNgay]

        if maSV_filter:
            sql += " AND sv.maSV = %s"
            params.append(maSV_filter)

        sql += """
            GROUP BY
                sv.maSV, sv.hoTen, dv.maDV, dv.tenDV
            ORDER BY
                sv.maSV, dv.tenDV;
        """
        cursor.execute(sql, tuple(params))
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)

    except Exception as e:
        print(f"Lỗi báo cáo sử dụng dịch vụ: {e}")
        return jsonify({"error": "Lỗi máy chủ khi tạo báo cáo"}), 500
    finally:
        if cursor: cursor.close()


# --- API Báo cáo 3: Khách thăm sinh viên ---
@bp.route('/khach-tham', methods=['GET'])
def report_khach_tham():
    tuNgay = request.args.get('tuNgay') # YYYY-MM-DD
    denNgay = request.args.get('denNgay') # YYYY-MM-DD
    if not tuNgay or not denNgay:
         return jsonify({"error": "Thiếu tham số 'tuNgay' hoặc 'denNgay' (YYYY-MM-DD)"}), 400

    cache_key = f"report:khachtham:{tuNgay}:{denNgay}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # Query 3
        sql = """
            SELECT
                sv.maSV,
                sv.hoTen AS TenSinhVien,
                k.hoTen AS TenKhach,
                k.soCMT AS CMTKhach,
                COUNT(tk.maTham) AS SoLanDen
            FROM
                tblSinhVien sv
            JOIN tblThamKhach tk ON sv.maSV = tk.maSV
            JOIN tblKhach k ON tk.maKhach = k.maKhach
            WHERE
                tk.thoiGianVao >= %s
                AND tk.thoiGianVao < DATE_ADD(%s, INTERVAL 1 DAY)
            GROUP BY
                sv.maSV, sv.hoTen, k.maKhach, k.hoTen, k.soCMT
            ORDER BY
                sv.maSV, k.hoTen;
        """
        params = (tuNgay, denNgay)
        cursor.execute(sql, params)
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)

    except Exception as e:
        print(f"Lỗi báo cáo khách thăm: {e}")
        return jsonify({"error": "Lỗi máy chủ khi tạo báo cáo"}), 500
    finally:
        if cursor: cursor.close()


# --- API Báo cáo 4: Doanh thu dịch vụ hàng tháng ---
@bp.route('/doanh-thu-dich-vu', methods=['GET'])
def report_doanh_thu_dich_vu():
    thangXem = request.args.get('thang') # YYYY-MM
    if not thangXem:
        return jsonify({"error": "Thiếu tham số 'thang' (YYYY-MM)"}), 400

    try:
        ngayDauThang = date.fromisoformat(f"{thangXem}-01")
        # Tính ngày đầu tháng sau để so sánh "<"
        if ngayDauThang.month == 12:
            ngayDauThangSau = date(ngayDauThang.year + 1, 1, 1)
        else:
            ngayDauThangSau = date(ngayDauThang.year, ngayDauThang.month + 1, 1)
    except ValueError:
         return jsonify({"error": "Định dạng tháng không hợp lệ (YYYY-MM)"}), 400

    cache_key = f"report:doanhthudv:{thangXem}"
    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # Query 4
        sql = """
            SELECT
                DATE_FORMAT(sdv.thoiGianSuDung, '%Y-%m') AS ThangNam,
                ldv.tenLoaiDV,
                dv.tenDV,
                SUM(sdv.thanhTien) AS DoanhThu
            FROM
                tblSuDungDichVu sdv
            JOIN tblDichVu dv ON sdv.maDV = dv.maDV
            JOIN tblLoaiDichVu ldv ON dv.maLoaiDV = ldv.maLoaiDV
            WHERE
                sdv.thoiGianSuDung >= %s AND sdv.thoiGianSuDung < %s
            GROUP BY
                ThangNam, ldv.maLoaiDV, ldv.tenLoaiDV, dv.maDV, dv.tenDV
            ORDER BY
                ThangNam DESC, ldv.tenLoaiDV, DoanhThu DESC;
        """
        params = (ngayDauThang, ngayDauThangSau)
        cursor.execute(sql, params)
        result = cursor.fetchall()
        set_cache(cache_key, result)
        return jsonify(result)

    except Exception as e:
        print(f"Lỗi báo cáo doanh thu dịch vụ tháng {thangXem}: {e}")
        return jsonify({"error": "Lỗi máy chủ khi tạo báo cáo"}), 500
    finally:
        if cursor: cursor.close()