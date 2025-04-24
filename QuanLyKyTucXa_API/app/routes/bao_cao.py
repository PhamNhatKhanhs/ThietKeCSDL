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

    try:
        # Xác định ngày đầu và cuối tháng
        namXem = int(thangXem.split('-')[0])
        thangXem_INT = int(thangXem.split('-')[1])
        ngayDauThang = date(namXem, thangXem_INT, 1)
        # Ngày cuối tháng phức tạp hơn một chút để xử lý tháng 2 và các tháng khác nhau
        if thangXem_INT == 12:
             ngayCuoiThang = date(namXem, thangXem_INT, 31)
        else:
             ngayCuoiThang = date(namXem, thangXem_INT + 1, 1) - timedelta(days=1)

    except ValueError:
         return jsonify({"error": "Định dạng tháng không hợp lệ (YYYY-MM)"}), 400

    # Cache key có thể bao gồm cả tháng và mã SV nếu lọc
    cache_key = f"report:chiphi:{thangXem}"
    if maSV_filter:
        cache_key += f":{maSV_filter}"

    cached_data = get_cache(cache_key)
    if cached_data: return jsonify(cached_data)

    cursor = None
    try:
        cursor = get_cursor(dictionary=True)
        if not cursor: return jsonify({"error": "Lỗi kết nối CSDL"}), 500

        # Tái sử dụng hoặc điều chỉnh Query 1 từ script SQL bạn đã có
        # Query này khá phức tạp, cần đảm bảo nó hoạt động đúng
        sql = """
            SELECT
                sv.maSV,
                sv.hoTen,
                %s AS ThangNam,
                -- Tiền phòng
                IFNULL(tp.donGiaThang, 0) AS TienPhong,
                -- Tiền dịch vụ
                IFNULL(tdv.TongTienDV, 0) AS TienDichVu,
                -- Tiền gửi xe tháng
                IFNULL(tgx_thang.TongPhiThang, 0) AS TienGuiXe_PhiThang,
                 -- Tiền phạt gửi xe
                IFNULL(tgx_phat.TongPhiPhat, 0) AS TienGuiXe_Phat,
                -- Tổng cộng
                (IFNULL(tp.donGiaThang, 0) +
                 IFNULL(tdv.TongTienDV, 0) +
                 IFNULL(tgx_thang.TongPhiThang, 0) +
                 IFNULL(tgx_phat.TongPhiPhat, 0)
                ) AS TongCongThang
            FROM
                tblSinhVien sv
            -- Lấy tiền phòng (chỉ lấy 1 phòng nếu SV đang thuê)
            LEFT JOIN (
                SELECT hd.maSV, lp.donGiaThang
                FROM tblHopDongThuePhong hd
                JOIN tblPhong p ON hd.maPhong = p.maPhong
                JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
                WHERE hd.trangThai = 'Đang thuê'
                  AND hd.ngayBatDau <= %s -- LAST_DAY
                  AND (hd.ngayKetThuc IS NULL OR hd.ngayKetThuc >= %s) -- First Day
                GROUP BY hd.maSV -- Đảm bảo chỉ lấy 1 giá phòng/SV
            ) tp ON sv.maSV = tp.maSV
            -- Lấy tổng tiền dịch vụ
            LEFT JOIN (
                SELECT maSV, SUM(thanhTien) AS TongTienDV
                FROM tblSuDungDichVu
                WHERE thoiGianSuDung >= %s AND thoiGianSuDung < DATE_ADD(%s, INTERVAL 1 MONTH)
                GROUP BY maSV
            ) tdv ON sv.maSV = tdv.maSV
            -- Lấy tổng phí gửi xe tháng
            LEFT JOIN (
                SELECT maSV, SUM(donGiaThang) AS TongPhiThang
                FROM tblDangKyGuiXeThang
                WHERE ngayDangKy <= %s
                  AND (ngayHetHan IS NULL OR ngayHetHan >= %s)
                GROUP BY maSV
            ) tgx_thang ON sv.maSV = tgx_thang.maSV
            -- Lấy tổng phí phạt gửi xe
            LEFT JOIN (
                 SELECT dgx.maSV, SUM(lgx.phiPhatSinh) AS TongPhiPhat
                 FROM tblLuotGuiLayXe lgx
                 JOIN tblDangKyGuiXeThang dgx ON lgx.maDangKy = dgx.maDangKy
                 WHERE lgx.ngay >= %s AND lgx.ngay <= %s
                 GROUP BY dgx.maSV
            ) tgx_phat ON sv.maSV = tgx_phat.maSV
            WHERE 1=1
        """
        params = [
            thangXem, ngayCuoiThang, ngayDauThang, # Cho tiền phòng
            ngayDauThang, ngayDauThang, # Cho tiền dịch vụ
            ngayCuoiThang, ngayDauThang, # Cho phí xe tháng
            ngayDauThang, ngayCuoiThang # Cho phí phạt
        ]

        if maSV_filter:
            sql += " AND sv.maSV = %s"
            params.append(maSV_filter)

        sql += " ORDER BY sv.maSV"

        cursor.execute(sql, tuple(params))
        result = cursor.fetchall()

        set_cache(cache_key, result)
        return jsonify(result)

    except Exception as e:
        print(f"Lỗi báo cáo chi phí sinh viên tháng {thangXem}: {e}")
        # In cả câu query và params để debug nếu cần
        # print("SQL:", sql)
        # print("Params:", params)
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