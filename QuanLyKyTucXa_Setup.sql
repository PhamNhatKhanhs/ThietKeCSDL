-- ==================================================================
-- Phần 0: THIẾT LẬP CƠ SỞ DỮ LIỆU
-- ==================================================================
DROP DATABASE IF EXISTS QuanLyKyTucXa;
CREATE DATABASE QuanLyKyTucXa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE QuanLyKyTucXa;

-- ==================================================================
-- Phần 1: TẠO BẢNG VÀ RÀNG BUỘC 
-- ==================================================================

CREATE TABLE tblSinhVien (
    maSV VARCHAR(10) PRIMARY KEY, -- Giả sử mã SV là VARCHAR
    hoTen NVARCHAR(100) NOT NULL,
    soCMT VARCHAR(12) UNIQUE NOT NULL,
    ngaySinh DATE,
    lop VARCHAR(50),
    queQuan NVARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblLoaiPhong (
    maLoaiPhong VARCHAR(10) PRIMARY KEY,
    tenLoai NVARCHAR(100) NOT NULL,
    donGiaThang DECIMAL(15, 2) NOT NULL,
    sucChua INT NOT NULL,
    moTa TEXT,
    CONSTRAINT chk_DonGiaThangLP CHECK (donGiaThang >= 0),
    CONSTRAINT chk_SucChuaLP CHECK (sucChua > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblPhong (
    maPhong VARCHAR(10) PRIMARY KEY,
    soPhong VARCHAR(10) UNIQUE NOT NULL,
    maLoaiPhong VARCHAR(10) NOT NULL,
    trangThai NVARCHAR(50) DEFAULT 'Sẵn sàng', -- Ví dụ: Sẵn sàng, Đang ở, Đang sửa chữa
    FOREIGN KEY (maLoaiPhong) REFERENCES tblLoaiPhong(maLoaiPhong) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblHopDongThuePhong (
    maHopDong VARCHAR(15) PRIMARY KEY,
    maSV VARCHAR(10) NOT NULL,
    maPhong VARCHAR(10) NOT NULL,
    ngayBatDau DATE NOT NULL,
    ngayKetThuc DATE, -- Có thể NULL nếu hợp đồng không thời hạn hoặc chưa xác định
    tienCoc DECIMAL(15, 2) DEFAULT 0,
    trangThai NVARCHAR(50) DEFAULT 'Đang thuê', -- Ví dụ: Đang thuê, Đã kết thúc, Đã hủy
    FOREIGN KEY (maSV) REFERENCES tblSinhVien(maSV) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (maPhong) REFERENCES tblPhong(maPhong) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_NgayHopDong CHECK (ngayKetThuc IS NULL OR ngayKetThuc >= ngayBatDau)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblKhach (
    maKhach INT AUTO_INCREMENT PRIMARY KEY,
    hoTen NVARCHAR(100) NOT NULL,
    soCMT VARCHAR(12) UNIQUE, -- CMT có thể không bắt buộc hoặc không unique tùy quy định
    ngaySinh DATE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblThamKhach (
    maTham BIGINT AUTO_INCREMENT PRIMARY KEY,
    maKhach INT NOT NULL,
    maSV VARCHAR(10) NOT NULL,
    thoiGianVao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    thoiGianRa DATETIME,
    ghiChu TEXT,
    FOREIGN KEY (maKhach) REFERENCES tblKhach(maKhach) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (maSV) REFERENCES tblSinhVien(maSV) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_ThoiGianTham CHECK (thoiGianRa IS NULL OR thoiGianRa >= thoiGianVao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblLoaiDichVu (
    maLoaiDV VARCHAR(10) PRIMARY KEY,
    tenLoaiDV NVARCHAR(100) NOT NULL,
    moTa TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblDichVu (
    maDV VARCHAR(10) PRIMARY KEY,
    maLoaiDV VARCHAR(10) NOT NULL,
    tenDV NVARCHAR(100) UNIQUE NOT NULL,
    donGia DECIMAL(15, 2) NOT NULL,
    donViTinh NVARCHAR(50),
    FOREIGN KEY (maLoaiDV) REFERENCES tblLoaiDichVu(maLoaiDV) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_DonGiaDV CHECK (donGia >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblSuDungDichVu (
    maSuDung BIGINT AUTO_INCREMENT PRIMARY KEY,
    maSV VARCHAR(10) NOT NULL,
    maDV VARCHAR(10) NOT NULL,
    thoiGianSuDung DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    soLuong INT DEFAULT 1,
    thanhTien DECIMAL(15, 2) NOT NULL, -- Tính toán = soLuong * donGia DV tại thời điểm sử dụng
    FOREIGN KEY (maSV) REFERENCES tblSinhVien(maSV) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (maDV) REFERENCES tblDichVu(maDV) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_SoLuongSD CHECK (soLuong > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblXe (
    bienSoXe VARCHAR(15) PRIMARY KEY,
    maSV VARCHAR(10) NOT NULL,
    loaiXe NVARCHAR(50),
    mauSac NVARCHAR(50),
    ghiChu TEXT,
    FOREIGN KEY (maSV) REFERENCES tblSinhVien(maSV) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblDangKyGuiXeThang (
    maDangKy VARCHAR(20) PRIMARY KEY,
    maSV VARCHAR(10) NOT NULL,
    bienSoXe VARCHAR(15) NOT NULL,
    ngayDangKy DATE NOT NULL,
    ngayHetHan DATE, -- NULL nếu là vé không thời hạn? Hoặc luôn có hạn
    donGiaThang DECIMAL(15, 2) DEFAULT 100000, -- Giá cố định theo yêu cầu
    FOREIGN KEY (maSV) REFERENCES tblSinhVien(maSV) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (bienSoXe) REFERENCES tblXe(bienSoXe) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_NgayDangKyXe CHECK (ngayHetHan IS NULL OR ngayHetHan >= ngayDangKy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblLuotGuiLayXe (
    maLuot BIGINT AUTO_INCREMENT PRIMARY KEY,
    maDangKy VARCHAR(20) NOT NULL,
    ngay DATE NOT NULL, -- Ngày thực hiện để kiểm tra giới hạn
    thoiGianVao DATETIME, -- Có thể vào mà chưa ra
    thoiGianRa DATETIME, -- Có thể ra mà chưa vào (nếu logic cho phép)
    phiPhatSinh DECIMAL(15, 2) DEFAULT 0, -- 0 hoặc 3000
    FOREIGN KEY (maDangKy) REFERENCES tblDangKyGuiXeThang(maDangKy) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_ThoiGianGuiLay CHECK (thoiGianRa IS NULL OR thoiGianVao IS NULL OR thoiGianRa >= thoiGianVao)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tblHoaDonThanhToan (
    maHoaDon VARCHAR(20) PRIMARY KEY,
    maSV VARCHAR(10) NOT NULL,
    kyHoaDonTuNgay DATE NOT NULL,
    kyHoaDonDenNgay DATE NOT NULL,
    ngayLap DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tongTienPhong DECIMAL(15, 2) DEFAULT 0,
    tongTienDichVu DECIMAL(15, 2) DEFAULT 0,
    tongTienGuiXe DECIMAL(15, 2) DEFAULT 0,
    tongCong DECIMAL(15, 2) DEFAULT 0,
    ngayThanhToan DATETIME,
    trangThai NVARCHAR(50) DEFAULT 'Chưa thanh toán', -- Ví dụ: Chưa thanh toán, Đã thanh toán
    FOREIGN KEY (maSV) REFERENCES tblSinhVien(maSV) ON DELETE RESTRICT ON UPDATE CASCADE, -- Hạn chế xóa SV nếu còn hóa đơn
    CONSTRAINT chk_KyHoaDon CHECK (kyHoaDonDenNgay >= kyHoaDonTuNgay)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================================================================
-- Phần 2: NHẬP DỮ LIỆU MẪU
-- ==================================================================
-- Dữ liệu cần bao gồm các tháng khác nhau (ví dụ: 2025-03, 2025-04, 2025-05)

-- Sinh viên
INSERT INTO tblSinhVien (maSV, hoTen, soCMT, ngaySinh, lop, queQuan) VALUES
('SV001', 'Nguyễn Văn An', '123456789001', '2003-05-10', 'CNTT65A', 'Hà Nội'),
('SV002', 'Trần Thị Bình', '123456789002', '2004-02-15', 'KT66B', 'Hải Phòng'),
('SV003', 'Lê Văn Cường', '123456789003', '2003-11-25', 'NN65C', 'Đà Nẵng'),
('SV004', 'Phạm Thị Dung', '123456789004', '2004-08-30', 'QTKD66D', 'TP. HCM');

-- Loại phòng
INSERT INTO tblLoaiPhong (maLoaiPhong, tenLoai, donGiaThang, sucChua, moTa) VALUES
('LP01', 'Phòng thường 4 người', 1000000, 4, 'Phòng tiêu chuẩn, vệ sinh chung'),
('LP02', 'Phòng dịch vụ 2 người', 2500000, 2, 'Phòng khép kín, có điều hòa'),
('LP03', 'Phòng thường 6 người', 800000, 6, 'Phòng tiêu chuẩn lớn');

-- Phòng
INSERT INTO tblPhong (maPhong, soPhong, maLoaiPhong, trangThai) VALUES
('P101', '101', 'LP01', 'Đang ở'),
('P102', '102', 'LP01', 'Đang ở'),
('P201', '201', 'LP02', 'Đang ở'),
('P202', '202', 'LP02', 'Sẵn sàng'),
('P301', '301', 'LP03', 'Đang ở');

-- Hợp đồng thuê phòng
INSERT INTO tblHopDongThuePhong (maHopDong, maSV, maPhong, ngayBatDau, ngayKetThuc, trangThai) VALUES
('HD001', 'SV001', 'P101', '2024-09-01', '2025-08-31', 'Đang thuê'),
('HD002', 'SV002', 'P101', '2024-09-01', '2025-08-31', 'Đang thuê'),
('HD003', 'SV003', 'P201', '2024-10-01', NULL, 'Đang thuê'), -- Hợp đồng không thời hạn
('HD004', 'SV004', 'P102', '2025-03-01', '2025-06-30', 'Đang thuê'); -- Hợp đồng mới hơn


-- Khách
INSERT INTO tblKhach (hoTen, soCMT, ngaySinh) VALUES
('Nguyễn Thị Lan', '987654321001', '2003-06-12'),
('Trần Văn Mạnh', '987654321002', '1980-01-01'); -- Bố/Mẹ

-- Thăm khách
-- SV001 được thăm 2 lần bởi khách 1 trong tháng 4
INSERT INTO tblThamKhach (maKhach, maSV, thoiGianVao, thoiGianRa) VALUES
(1, 'SV001', '2025-04-05 14:00:00', '2025-04-05 16:00:00'),
(1, 'SV001', '2025-04-12 09:30:00', '2025-04-12 11:00:00'),
-- SV003 được thăm 1 lần bởi khách 2 trong tháng 4
(2, 'SV003', '2025-04-20 19:00:00', '2025-04-20 20:30:00'),
-- SV001 được thăm trong tháng 5
(1, 'SV001', '2025-05-01 10:00:00', NULL); -- Chưa ra


-- Loại dịch vụ
INSERT INTO tblLoaiDichVu (maLoaiDV, tenLoaiDV) VALUES
('DV_AN', 'Dịch vụ Ăn uống'),
('DV_GIAT', 'Dịch vụ Giặt là'),
('DV_XE', 'Dịch vụ Xe cộ');

-- Dịch vụ
INSERT INTO tblDichVu (maDV, maLoaiDV, tenDV, donGia, donViTinh) VALUES
('AN_COM', 'DV_AN', 'Suất cơm trưa/tối', 30000, 'Suất'),
('GIAT_KG', 'DV_GIAT', 'Giặt sấy theo Kg', 10000, 'Kg'),
('GIAT_AO', 'DV_GIAT', 'Giặt áo sơ mi', 15000, 'Chiếc'),
('XE_THUE', 'DV_XE', 'Thuê xe đạp theo giờ', 5000, 'Giờ');

-- Sử dụng dịch vụ
-- Tháng 3/2025
INSERT INTO tblSuDungDichVu (maSV, maDV, thoiGianSuDung, soLuong, thanhTien) VALUES
('SV001', 'AN_COM', '2025-03-10 12:00:00', 1, 30000),
('SV003', 'GIAT_KG', '2025-03-15 08:00:00', 3, 30000);
-- Tháng 4/2025
INSERT INTO tblSuDungDichVu (maSV, maDV, thoiGianSuDung, soLuong, thanhTien) VALUES
('SV001', 'AN_COM', '2025-04-01 18:00:00', 1, 30000),
('SV001', 'GIAT_AO', '2025-04-05 09:00:00', 2, 30000),
('SV002', 'AN_COM', '2025-04-10 12:00:00', 1, 30000),
('SV003', 'GIAT_KG', '2025-04-11 10:00:00', 2, 20000),
('SV003', 'XE_THUE', '2025-04-20 14:00:00', 3, 15000), -- Thuê 3 giờ
('SV004', 'AN_COM', '2025-04-22 12:00:00', 1, 30000);
-- Tháng 5/2025
INSERT INTO tblSuDungDichVu (maSV, maDV, thoiGianSuDung, soLuong, thanhTien) VALUES
('SV001', 'AN_COM', '2025-05-01 12:00:00', 1, 30000);

-- Xe
INSERT INTO tblXe (bienSoXe, maSV, loaiXe, mauSac) VALUES
('29A1-12345', 'SV001', 'Xe máy', 'Đen'),
('30B2-67890', 'SV003', 'Xe máy', 'Trắng'),
('HN-XĐ-001', 'SV001', 'Xe đạp', 'Xanh'); -- SV001 có 2 xe

-- Đăng ký gửi xe tháng
INSERT INTO tblDangKyGuiXeThang (maDangKy, maSV, bienSoXe, ngayDangKy, ngayHetHan, donGiaThang) VALUES
('DKX001', 'SV001', '29A1-12345', '2024-09-01', '2025-08-31', 100000),
('DKX002', 'SV003', '30B2-67890', '2024-10-01', NULL, 100000),
('DKX003', 'SV001', 'HN-XĐ-001', '2025-04-01', '2025-06-30', 100000); -- Đăng ký mới tháng 4

-- Lượt gửi lấy xe
-- Tháng 3/2025
INSERT INTO tblLuotGuiLayXe (maDangKy, ngay, thoiGianVao, thoiGianRa, phiPhatSinh) VALUES
('DKX001', '2025-03-05', '2025-03-05 07:00:00', '2025-03-05 17:00:00', 0), -- Lượt 1
('DKX001', '2025-03-05', '2025-03-05 19:00:00', '2025-03-05 21:00:00', 0); -- Lượt 2
-- Tháng 4/2025
-- Xe 1 (DKX001) của SV001: 3 lượt trong ngày 2025-04-10 -> 1 lượt phạt
INSERT INTO tblLuotGuiLayXe (maDangKy, ngay, thoiGianVao, thoiGianRa, phiPhatSinh) VALUES
('DKX001', '2025-04-10', '2025-04-10 07:00:00', '2025-04-10 09:00:00', 0), -- Lượt 1
('DKX001', '2025-04-10', '2025-04-10 11:00:00', '2025-04-10 13:00:00', 0), -- Lượt 2
('DKX001', '2025-04-10', '2025-04-10 17:00:00', '2025-04-10 19:00:00', 3000); -- Lượt 3 -> Phạt
-- Xe 2 (DKX003) của SV001: 1 lượt
INSERT INTO tblLuotGuiLayXe (maDangKy, ngay, thoiGianVao, thoiGianRa, phiPhatSinh) VALUES
('DKX003', '2025-04-15', '2025-04-15 08:00:00', '2025-04-15 16:00:00', 0);
-- Xe của SV003 (DKX002): 2 lượt
INSERT INTO tblLuotGuiLayXe (maDangKy, ngay, thoiGianVao, thoiGianRa, phiPhatSinh) VALUES
('DKX002', '2025-04-18', '2025-04-18 07:30:00', '2025-04-18 11:30:00', 0),
('DKX002', '2025-04-18', '2025-04-18 13:30:00', '2025-04-18 17:30:00', 0);

-- (Tùy chọn) Tạo hóa đơn mẫu (Thường việc tạo hóa đơn sẽ do ứng dụng làm)
-- INSERT INTO tblHoaDonThanhToan (...) VALUES (...);

-- ==================================================================
-- Phần 3: CÁC CÂU LỆNH TRUY VẤN THEO YÊU CẦU
-- ==================================================================

-- ------------------------------------------------------------------
-- TRUY VẤN 1: Liệt kê thông tin sinh viên và tổng tiền phải trả mỗi tháng.
-- ------------------------------------------------------------------
-- Đặt biến cho tháng cần xem (ví dụ: tháng 4 năm 2025)
SET @ThangXem = '2025-04';
SET @NamXem = YEAR(STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d'));
SET @ThangXem_INT = MONTH(STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d'));

SELECT
    sv.maSV,
    sv.hoTen,
    @ThangXem AS ThangNam,
    -- Tính tiền phòng (Logic "chẵn tháng")
    IFNULL((
        SELECT lp.donGiaThang
        FROM tblHopDongThuePhong hd
        JOIN tblPhong p ON hd.maPhong = p.maPhong
        JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
        WHERE hd.maSV = sv.maSV
          AND hd.trangThai = 'Đang thuê'
          AND hd.ngayBatDau <= LAST_DAY(STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d')) -- Bắt đầu trước hoặc trong tháng
          AND (hd.ngayKetThuc IS NULL OR hd.ngayKetThuc >= STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d')) -- Kết thúc trong hoặc sau tháng (hoặc chưa kết thúc)
        LIMIT 1 -- Giả sử mỗi SV chỉ có 1 hợp đồng active tại 1 thời điểm
    ), 0) AS TienPhong,

    -- Tính tiền dịch vụ
    IFNULL(SUM(sdv.thanhTien), 0) AS TienDichVu,

    -- Tính tiền gửi xe tháng
    IFNULL(SUM(dgx.donGiaThang), 0) AS TienGuiXe_PhiThang,

    -- Tính tiền phạt gửi xe
    IFNULL(SUM(lgx.phiPhatSinh), 0) AS TienGuiXe_Phat,

    -- Tổng cộng
    (IFNULL((
        SELECT lp.donGiaThang
        FROM tblHopDongThuePhong hd
        JOIN tblPhong p ON hd.maPhong = p.maPhong
        JOIN tblLoaiPhong lp ON p.maLoaiPhong = lp.maLoaiPhong
        WHERE hd.maSV = sv.maSV
          AND hd.trangThai = 'Đang thuê'
           AND hd.ngayBatDau <= LAST_DAY(STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d'))
          AND (hd.ngayKetThuc IS NULL OR hd.ngayKetThuc >= STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d'))
        LIMIT 1
    ), 0)
    + IFNULL(SUM(sdv.thanhTien), 0)
    + IFNULL(SUM(dgx.donGiaThang), 0)
    + IFNULL(SUM(lgx.phiPhatSinh), 0)
    ) AS TongCongThang
FROM
    tblSinhVien sv
LEFT JOIN tblSuDungDichVu sdv ON sv.maSV = sdv.maSV AND DATE_FORMAT(sdv.thoiGianSuDung, '%Y-%m') = @ThangXem
LEFT JOIN tblDangKyGuiXeThang dgx ON sv.maSV = dgx.maSV
    AND dgx.ngayDangKy <= LAST_DAY(STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d'))
    AND (dgx.ngayHetHan IS NULL OR dgx.ngayHetHan >= STR_TO_DATE(CONCAT(@ThangXem, '-01'), '%Y-%m-%d'))
LEFT JOIN tblLuotGuiLayXe lgx ON dgx.maDangKy = lgx.maDangKy AND DATE_FORMAT(lgx.ngay, '%Y-%m') = @ThangXem
GROUP BY
    sv.maSV, sv.hoTen
ORDER BY
    sv.maSV;

-- ------------------------------------------------------------------
-- TRUY VẤN 2: Liệt kê thông tin sinh viên, tên dịch vụ, tổng giá mỗi dịch vụ sử dụng trong khoảng thời gian.
-- ------------------------------------------------------------------
SET @NgayBatDau = '2025-04-01';
SET @NgayKetThuc = '2025-04-30';
-- SET @MaSinhVienCuThe = 'SV001'; -- Bỏ comment nếu muốn lọc theo 1 SV

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
    sdv.thoiGianSuDung >= @NgayBatDau
    AND sdv.thoiGianSuDung < DATE_ADD(@NgayKetThuc, INTERVAL 1 DAY) -- Để bao gồm cả ngày kết thúc
    -- AND sv.maSV = @MaSinhVienCuThe -- Bỏ comment nếu muốn lọc theo 1 SV
GROUP BY
    sv.maSV, sv.hoTen, dv.maDV, dv.tenDV
ORDER BY
    sv.maSV, dv.tenDV;

-- ------------------------------------------------------------------
-- TRUY VẤN 3: Liệt kê thông tin sinh viên, khách đến thăm và số lần thăm trong khoảng thời gian.
-- ------------------------------------------------------------------
-- Xem theo tuần này (Ví dụ)
SET @NgayBatDauTuan = DATE_SUB(CURDATE(), INTERVAL DAYOFWEEK(CURDATE())-2 DAY); -- Thứ 2 tuần này
SET @NgayKetThucTuan = DATE_ADD(@NgayBatDauTuan, INTERVAL 6 DAY); -- Chủ nhật tuần này

-- Xem theo tháng (Ví dụ tháng 4/2025)
SET @NgayBatDauThang = '2025-04-01';
SET @NgayKetThucThang = '2025-04-30';

SELECT
    sv.maSV,
    sv.hoTen AS TenSinhVien,
    k.hoTen AS TenKhach,
    COUNT(tk.maTham) AS SoLanDen
FROM
    tblSinhVien sv
JOIN tblThamKhach tk ON sv.maSV = tk.maSV
JOIN tblKhach k ON tk.maKhach = k.maKhach
WHERE
    tk.thoiGianVao >= @NgayBatDauThang -- Thay bằng @NgayBatDauTuan nếu xem theo tuần
    AND tk.thoiGianVao < DATE_ADD(@NgayKetThucThang, INTERVAL 1 DAY) -- Thay bằng @NgayKetThucTuan nếu xem theo tuần
GROUP BY
    sv.maSV, sv.hoTen, k.maKhach, k.hoTen
ORDER BY
    sv.maSV, k.hoTen;

-- ------------------------------------------------------------------
-- TRUY VẤN 4: Liệt kê danh mục dịch vụ và doanh thu mỗi dịch vụ mỗi tháng.
-- ------------------------------------------------------------------
SELECT
    DATE_FORMAT(sdv.thoiGianSuDung, '%Y-%m') AS ThangNam,
    ldv.tenLoaiDV,
    dv.tenDV,
    SUM(sdv.thanhTien) AS DoanhThu
FROM
    tblSuDungDichVu sdv
JOIN tblDichVu dv ON sdv.maDV = dv.maDV
JOIN tblLoaiDichVu ldv ON dv.maLoaiDV = ldv.maLoaiDV
GROUP BY
    ThangNam, ldv.maLoaiDV, ldv.tenLoaiDV, dv.maDV, dv.tenDV
ORDER BY
    ThangNam DESC, ldv.tenLoaiDV, DoanhThu DESC;

-- ==================================================================
-- Phần 4: THỂ HIỆN VIỆC KIỂM TRA RÀNG BUỘC (Ví dụ bằng mô tả)
-- ==================================================================

-- 1. Ràng buộc số người trong phòng:
--    Khi thêm mới một bản ghi vào `tblHopDongThuePhong`:
--    - Bước 1: Lấy `maPhong` từ bản ghi sắp thêm.
--    - Bước 2: Truy vấn `tblLoaiPhong` để lấy `sucChua` dựa trên `maLoaiPhong` của phòng đó.
--    - Bước 3: Truy vấn `tblHopDongThuePhong` để đếm số hợp đồng đang có `trangThai = 'Đang thuê'` cho `maPhong` đó.
--    - Bước 4: So sánh số lượng đếm được với `sucChua`. Nếu số lượng < `sucChua` thì cho phép thêm mới, ngược lại thông báo lỗi "Phòng đã đủ người".
--    *Ví dụ kiểm tra phòng P101 (loại LP01, sức chứa 4):*
--      SELECT COUNT(*) FROM tblHopDongThuePhong WHERE maPhong = 'P101' AND trangThai = 'Đang thuê'; -- Hiện tại trả về 2
--      SELECT sucChua FROM tblLoaiPhong WHERE maLoaiPhong = 'LP01'; -- Trả về 4
--      => 2 < 4 => Có thể thêm người.

-- 2. Ràng buộc số xe tháng tối đa của sinh viên (tối đa 2):
--    Khi thêm mới một bản ghi vào `tblDangKyGuiXeThang`:
--    - Bước 1: Lấy `maSV` từ bản ghi sắp thêm.
--    - Bước 2: Truy vấn `tblDangKyGuiXeThang` để đếm số đăng ký đang còn hiệu lực (ví dụ: `ngayHetHan IS NULL OR ngayHetHan >= CURDATE()`) cho `maSV` đó.
--    - Bước 3: So sánh số lượng đếm được với 2. Nếu số lượng < 2 thì cho phép thêm mới, ngược lại thông báo lỗi "Sinh viên đã đăng ký đủ 2 xe".
--    *Ví dụ kiểm tra SV001:*
--      SELECT COUNT(*) FROM tblDangKyGuiXeThang
--      WHERE maSV = 'SV001' AND (ngayHetHan IS NULL OR ngayHetHan >= CURDATE()); -- Hiện tại trả về 2 (DKX001 còn hạn, DKX003 còn hạn)
--      => 2 < 2 là FALSE => Không thể đăng ký thêm xe.

-- 3. Ràng buộc số lượt gửi/lấy xe miễn phí (2 lượt/ngày):
--    Khi thêm mới một bản ghi vào `tblLuotGuiLayXe` (hoặc khi xe ra/vào):
--    - Bước 1: Lấy `maDangKy` và `ngay` hiện tại.
--    - Bước 2: Truy vấn `tblLuotGuiLayXe` để đếm số lượt đã thực hiện cho `maDangKy` đó trong `ngay` đó.
--    - Bước 3: Nếu số lượt đếm được >= 2 thì khi thêm bản ghi mới, đặt `phiPhatSinh = 3000`, ngược lại đặt `phiPhatSinh = 0`.
--    *Ví dụ kiểm tra DKX001 ngày 2025-04-10:*
--      SELECT COUNT(*) FROM tblLuotGuiLayXe WHERE maDangKy = 'DKX001' AND ngay = '2025-04-10'; -- Trả về 3
--      => Nếu có lượt thứ 4 trong ngày này thì phiPhatSinh = 3000.

-- ==================================================================
-- Kết thúc script
-- ==================================================================