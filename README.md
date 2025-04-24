# Hệ thống Quản lý Ký túc xá API (Project 2)

Đây là dự án backend API được xây dựng để quản lý các hoạt động và thông tin trong một ký túc xá sinh viên, bao gồm quản lý sinh viên, phòng ở, hợp đồng, dịch vụ, gửi xe, khách thăm và hóa đơn thanh toán.

## Mô tả

Ứng dụng cung cấp các API endpoints theo chuẩn RESTful để thực hiện các thao tác CRUD (Create, Read, Update, Delete) cơ bản đối với các đối tượng dữ liệu chính, đồng thời cung cấp các API để thực hiện các truy vấn, báo cáo phức tạp theo yêu cầu nghiệp vụ. Hệ thống cũng tích hợp Redis để caching dữ liệu, giúp tăng tốc độ truy cập cho các yêu cầu đọc thông tin thường xuyên. Logic kiểm tra các ràng buộc nghiệp vụ (như số người tối đa/phòng, số xe tối đa/sinh viên) được tích hợp vào tầng service của ứng dụng.

## Tính năng chính

* Quản lý Thông tin Sinh viên (CRUD)
* Quản lý Loại phòng, Phòng ở (CRUD)
* Quản lý Hợp đồng Thuê phòng (CRUD, kiểm tra phòng trống)
* Quản lý Loại dịch vụ, Dịch vụ (CRUD)
* Quản lý Ghi nhận Sử dụng Dịch vụ (Tạo, đọc lịch sử)
* Quản lý Xe, Đăng ký Gửi xe Tháng (CRUD, kiểm tra giới hạn xe)
* Quản lý Lượt Gửi/Lấy Xe (Tạo với tính phí phạt tự động, đọc lịch sử)
* Quản lý Khách, Ghi nhận Lượt thăm (Tạo/Tìm khách, Tạo lượt thăm, Ghi nhận khách ra)
* Quản lý Hóa đơn Thanh toán (Tạo tự động hàng tháng, Xem, Cập nhật trạng thái thanh toán)
* API Báo cáo/Truy vấn phức tạp theo yêu cầu.
* Tích hợp Redis Caching cho các API GET để tăng hiệu năng.

## Công nghệ sử dụng

* **Ngôn ngữ:** Python 3
* **Framework:** Flask
* **Cơ sở dữ liệu:** MySQL 8.0+
* **Caching:** Redis
* **Thư viện Python chính:**
    * `Flask`
    * `mysql-connector-python`
    * `redis`
    * `python-dotenv`

## Thiết kế Cơ sở dữ liệu (ERD - Mermaid)

```mermaid
erDiagram
    tblSinhVien {
        VARCHAR maSV PK "Mã Sinh Viên"
        NVARCHAR hoTen "Họ tên"
        VARCHAR soCMT UK "Số CMT/CCCD (Unique)"
        DATE ngaySinh "Ngày sinh"
        VARCHAR lop "Lớp"
        NVARCHAR queQuan "Quê quán"
    }
    tblLoaiPhong {
        VARCHAR maLoaiPhong PK "Mã loại phòng"
        NVARCHAR tenLoai "Tên loại phòng"
        DECIMAL donGiaThang "Đơn giá tháng"
        INT sucChua "Số người tối đa"
        TEXT moTa "Mô tả chi tiết"
    }
    tblPhong {
        VARCHAR maPhong PK "Mã Phòng (System ID)"
        VARCHAR soPhong UK "Số phòng (Tên phòng, Unique)"
        VARCHAR maLoaiPhong FK "Mã loại phòng"
        VARCHAR trangThai "Trạng thái phòng"
    }
    tblHopDongThuePhong {
        VARCHAR maHopDong PK "Mã Hợp đồng"
        VARCHAR maSV FK "Mã Sinh Viên"
        VARCHAR maPhong FK "Mã Phòng"
        DATE ngayBatDau "Ngày bắt đầu thuê"
        DATE ngayKetThuc "Ngày kết thúc thuê (dự kiến)"
        DECIMAL tienCoc "Tiền cọc"
        VARCHAR trangThai "Trạng thái (đang thuê, đã kết thúc)"
    }
    tblKhach {
        INT maKhach PK "Mã Khách (Auto Increment)"
        NVARCHAR hoTen "Họ tên khách"
        VARCHAR soCMT UK "Số CMT/CCCD khách (Unique)"
        DATE ngaySinh "Ngày sinh khách"
    }
    tblThamKhach {
        BIGINT maTham PK "Mã lần thăm (Auto Increment)"
        INT maKhach FK "Mã Khách"
        VARCHAR maSV FK "Mã SV được thăm"
        DATETIME thoiGianVao "Thời gian vào"
        DATETIME thoiGianRa "Thời gian ra (NULL nếu chưa ra)"
        TEXT ghiChu "Ghi chú"
    }
    tblLoaiDichVu {
        VARCHAR maLoaiDV PK "Mã loại dịch vụ"
        NVARCHAR tenLoaiDV "Tên loại dịch vụ"
        TEXT moTa "Mô tả"
    }
    tblDichVu {
        VARCHAR maDV PK "Mã Dịch vụ"
        VARCHAR maLoaiDV FK "Mã loại dịch vụ"
        NVARCHAR tenDV UK "Tên dịch vụ (Unique)"
        DECIMAL donGia "Đơn giá dịch vụ"
        VARCHAR donViTinh "Đơn vị tính"
    }
    tblSuDungDichVu {
        BIGINT maSuDung PK "Mã Lần sử dụng (Auto Increment)"
        VARCHAR maSV FK "Mã Sinh Viên"
        VARCHAR maDV FK "Mã Dịch vụ"
        DATETIME thoiGianSuDung "Thời điểm sử dụng"
        INT soLuong "Số lượng"
        DECIMAL thanhTien "Thành tiền lần sử dụng"
    }
    tblXe {
        VARCHAR bienSoXe PK "Biển số xe"
        VARCHAR maSV FK "Mã Sinh Viên sở hữu"
        NVARCHAR loaiXe "Loại xe (xe máy, xe đạp...)"
        NVARCHAR mauSac "Màu sắc"
        NVARCHAR ghiChu "Ghi chú thêm"
    }
    tblDangKyGuiXeThang {
        VARCHAR maDangKy PK "Mã Đăng ký gửi xe tháng"
        VARCHAR maSV FK "Mã Sinh Viên đăng ký"
        VARCHAR bienSoXe FK "Biển số xe đăng ký"
        DATE ngayDangKy "Ngày bắt đầu đăng ký"
        DATE ngayHetHan "Ngày hết hạn đăng ký"
        DECIMAL donGiaThang "Đơn giá theo tháng (100k)"
    }
    tblLuotGuiLayXe {
        BIGINT maLuot PK "Mã lượt (Auto Increment)"
        VARCHAR maDangKy FK "Mã Đăng ký xe tháng"
        DATE ngay "Ngày gửi/lấy xe"
        DATETIME thoiGianVao "Thời gian vào"
        DATETIME thoiGianRa "Thời gian ra (NULL đang trong ktx)"
        DECIMAL phiPhatSinh "Phí phát sinh (0 hoặc 3000)"
    }
    tblHoaDonThanhToan {
        VARCHAR maHoaDon PK "Mã Hóa đơn"
        VARCHAR maSV FK "Mã Sinh Viên"
        DATE kyHoaDonTuNgay "Kỳ hóa đơn từ ngày"
        DATE kyHoaDonDenNgay "Kỳ hóa đơn đến ngày"
        DATETIME ngayLap "Ngày lập hóa đơn"
        DECIMAL tongTienPhong "Tổng tiền phòng"
        DECIMAL tongTienDichVu "Tổng tiền dịch vụ"
        DECIMAL tongTienGuiXe "Tổng tiền gửi xe (phí tháng + phạt)"
        DECIMAL tongCong "Tổng cộng phải trả"
        DATETIME ngayThanhToan "Ngày đã thanh toán (NULL nếu chưa)"
        VARCHAR trangThai "Trạng thái (chưa/đã thanh toán)"
    }

    %% Define relationships
    tblSinhVien ||--o{ tblHopDongThuePhong : "ký"
    tblLoaiPhong ||--o{ tblPhong : "định nghĩa"
    tblPhong ||--o{ tblHopDongThuePhong : "được thuê trong"
    tblSinhVien ||--o{ tblThamKhach : "được thăm bởi"
    tblKhach ||--o{ tblThamKhach : "thực hiện thăm"
    tblLoaiDichVu ||--o{ tblDichVu : "phân loại"
    tblSinhVien ||--o{ tblSuDungDichVu : "sử dụng"
    tblDichVu ||--o{ tblSuDungDichVu : "được sử dụng trong"
    tblSinhVien ||--o{ tblXe : "sở hữu"
    tblXe ||--|{ tblDangKyGuiXeThang : "được đăng ký gửi"
    tblSinhVien ||--o{ tblDangKyGuiXeThang : "thực hiện đăng ký"
    tblDangKyGuiXeThang ||--o{ tblLuotGuiLayXe : "có các lượt"
    tblSinhVien ||--o{ tblHoaDonThanhToan : "thanh toán"

File Script CSDL
File QuanLyKyTucXa_Setup.sql trong repository này chứa đầy đủ các lệnh để:

Tạo cơ sở dữ liệu QuanLyKyTucXa.
Tạo tất cả các bảng với ràng buộc khóa chính, khóa ngoại, unique...
Chèn dữ liệu mẫu (INSERT) cho tất cả các bảng để kiểm thử.
Các câu lệnh truy vấn SQL phức tạp theo yêu cầu báo cáo của đề bài (được comment rõ ràng).
Hướng dẫn Cài đặt và Chạy
Yêu cầu hệ thống:

Python 3.8+
pip và venv (thường đi kèm Python)
MySQL Server (8.0+) đang chạy
Redis Server đang chạy
Các bước cài đặt:

Clone Repository:
Bash

git clone <URL_repository_cua_ban>
cd <Ten_thu_muc_repo>
Tạo và Kích hoạt Môi trường ảo:
Bash

python -m venv venv
# Trên Linux/macOS/WSL:
source venv/bin/activate
# Trên Windows (Command Prompt):
# venv\Scripts\activate.bat
# Trên Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
Cài đặt Dependencies:
Bash

pip install -r requirements.txt
Thiết lập Cơ sở dữ liệu:
Đảm bảo MySQL Server đang chạy.
Tạo một user và database riêng cho ứng dụng (khuyến nghị) hoặc sử dụng user root (nếu đang phát triển). Xem lại hướng dẫn tạo user ktx_app_user nếu cần.
Chạy file script SQL để tạo bảng và nhập dữ liệu mẫu (thay /duong/dan/toi/file.sql bằng đường dẫn thực tế):
Bash

# Đăng nhập vào mysql trước nếu cần, ví dụ: sudo mysql
# Hoặc chạy trực tiếp:
sudo mysql < /duong/dan/toi/QuanLyKyTucXa_Setup.sql
# Hoặc nếu dùng user khác root:
# mysql -u ten_user -p ten_database < /duong/dan/toi/QuanLyKyTucXa_Setup.sql
Cấu hình Biến Môi trường:
Tạo một file tên là .env trong thư mục gốc của dự án (cùng cấp với run.py).
Sao chép nội dung từ file .env.example (nếu bạn tạo file này) hoặc tự điền các giá trị sau vào file .env:
Ini, TOML

# .env file
MYSQL_HOST=localhost
MYSQL_USER=ktx_app_user        # Thay bằng user MySQL của bạn
MYSQL_PASSWORD=your_strong_password # Thay bằng mật khẩu MySQL của bạn
MYSQL_DB=QuanLyKyTucXa
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
FLASK_SECRET_KEY=thay_bang_mot_key_bi_mat_dai_ngoan_ngoèo
Quan trọng: Thay đổi các giá trị MYSQL_USER, MYSQL_PASSWORD, và FLASK_SECRET_KEY cho phù hợp với môi trường của bạn.
Chạy Ứng dụng:
Đảm bảo Redis server đang chạy (sudo systemctl start redis-server).
Chạy lệnh sau trong terminal (đã kích hoạt venv):
Bash

python run.py
Ứng dụng API sẽ chạy tại địa chỉ http://localhost:5000 (hoặc http://127.0.0.1:5000).
Tổng quan API Endpoints
Ứng dụng cung cấp các API endpoint với tiền tố /api. Các nhóm chính bao gồm:

/api/sinhvien: CRUD cho Sinh viên.
/api/loaiphong: CRUD cho Loại phòng.
/api/phong: CRUD cho Phòng.
/api/hopdong: Tạo hợp đồng (POST), lấy hợp đồng theo sinh viên (GET). (Có thể bổ sung PUT/DELETE).
/api/dichvu/loai: CRUD cho Loại dịch vụ.
/api/dichvu: CRUD cho Dịch vụ.
/api/dichvu/sudung: Ghi nhận sử dụng dịch vụ (POST), lấy lịch sử theo sinh viên (GET).
/api/guixe/xe: CRUD cho Xe. Lấy danh sách xe theo sinh viên (GET).
/api/guixe/dangky: CRUD cho Đăng ký gửi xe tháng. Lấy danh sách đăng ký theo sinh viên (GET).
/api/guixe/luot: Ghi nhận lượt gửi/lấy xe (POST). Lấy lịch sử lượt theo mã đăng ký (GET).
/api/khach: CRUD cho Khách. Tìm khách theo CMT (GET).
/api/khach/tham: Ghi nhận lượt thăm (POST), ghi nhận khách ra (PUT). Lấy lịch sử thăm theo sinh viên (GET).
/api/hoadon: Lấy danh sách/chi tiết hóa đơn (GET), cập nhật thanh toán (PUT), kích hoạt tạo hóa đơn tháng (POST).
/api/bao-cao: Các endpoint cho báo cáo (chi phí sinh viên, sử dụng dịch vụ, khách thăm, doanh thu dịch vụ).
Chi tiết về các tham số và body request/response có thể xem trực tiếp trong mã nguồn các file routes (app/routes/*.py).

Kiểm thử (Testing)
Sử dụng file test_api.sh (nếu có trong repo) để chạy các lệnh curl kiểm thử tự động:
Bash

chmod +x test_api.sh
./test_api.sh
Hoặc sử dụng các công cụ như Postman/Insomnia để gửi request thủ công đến các endpoint và kiểm tra kết quả. Tham khảo checklist kiểm thử đã thảo luận.
Đề bài / Yêu cầu Dự án (PROJECT 2)
(Sao chép lại toàn bộ nội dung đề bài PROJECT 2 vào đây)

YÊU CẦU CHUNG:

Xây dựng bản thiết kế CSDL với các thông tin và yêu cầu được cung cấp (có thể bổ sung để đầy đủ hơn).
Xây dựng bộ dữ liệu mẫu, thực thi CSDL trong Hệ quản trị CSDL và nhập các dữ liệu mẫu.
Viết các câu lệnh truy vấn theo yêu cầu.
Viết chương trình hoặc phát triển ứng dụng thao tác với CSDL (Có thể sử dụng Redis để tăng tốc độ truy cập).
YÊU CẦU NỘP: 1 file readme kèm theo repo cá nhân (Copy lại đề bài vào bên file readme)

Chọn 1 trong các đề bên dưới

Bản thiết kế CSDL (Readme (link hoặc ảnh)).
File script chứa các câu lệnh tạo bảng, nhập dữ liệu, và các câu lệnh truy vấn theo yêu cầu (Readme).
Viết API cho các thao tác CRUD cơ bản với mỗi đối tượng sử dụng 1 trong các ngôn ngữ Java, Python, JavaScript.
Viết API phục vụ các yêu cầu bên dưới mỗi đề bài
PROJECT 2:

Kịch bản thế giới thực: Xây dựng hệ thống quản lý ký túc xá sinh viên.

Các yêu cầu về CSDL bao gồm:

Thông tin về Sinh viên bao gồm Mã SV, số CMT, ngày sinh, lớp, quê quán.
Thông tin về phòng ở bao gồm số phòng, loại phòng, đơn giá, số người được ở tối đa trong phòng.
Các khách đến chơi trong KTX cũng cần phải được lưu thông tin gồm CMT, tên, ngày sinh, và thông tin của SV ở trong KTX mà khách đến chơi, ngày đến chơi.
Tiền thuê phòng được tính chẵn tháng, tức là ở một ngày cũng phải trả tiền cả tháng.
Các dịch vụ trong KTX gồm các thông tin về mã dịch vụ, tên dịch vụ, đơn giá, thời gian sử dụng dịch vụ. Mỗi sinh viên có thể sử dụng một hoặc nhiều dịch vụ. Một sinh viên có thể sử dụng một dịch vụ một hoặc nhiều lần. Tiền sử dụng dịch vụ được cộng dồn cho mỗi Sinh viên để cuối mỗi tháng gửi hoá đơn thanh toán cho từng sinh viên. Một số loại dịch vụ cơ bản trong KTX bao gồm giặt là, trông xe, cho thuê xe, ăn uống.
Sinh viên đăng ký gửi xe vé tháng trong KTX với đơn giá 100 nghìn một tháng. Trong mỗi ngày, một xe gửi tháng chỉ được lấy ra/gửi vào 2 lần miễn phí, mỗi lần lấy/gửi phát sinh phải mất tiền 3 nghìn đồng/lượt. Thông tin về các lần lấy/gửi xe cần phải được lưu lại bao gồm thời gian lấy xe, thời gian gửi xe, số tiền phải trả (nếu số lượt gửi/lấy xe vẫn còn trong hạn thì không mất tiền). Học viên cần tự xây dựng CSDL cho các xe được gửi và các thông tin về các lượt gửi/lấy xe, cùng thông tin về Sinh viên đăng ký gửi xe vé tháng. Mỗi sinh viên chỉ được đăng ký gửi tối đa 2 xe vé tháng.
Các xe không gửi vé tháng sẽ được tính tiền riêng cho mỗi lượt gửi/lấy xe và không cần lưu trong CSDL.
Các yêu cầu truy vấn:

Liệt kê thông tin sinh viên trong KTX cùng số tiền mà họ phải trả cho tất cả các dịch vụ (bao gồm cả tiền phòng) đã sử dụng trong mỗi tháng. Thông tin này có thể in theo danh sách hoặc theo từng người.
Liệt kê thông tin sinh viên cùng tên dịch vụ, tổng giá mỗi dịch vụ mà họ sử dụng trong khoảng thời gian từ ngày bắt đầu đến ngày kết thúc.   
Liệt kê thông tin sinh viên cùng thông tin về các khách đến thăm họ trong tuần, hoặc tháng, cùng số lần mỗi khách đến chơi.
Liệt kê danh mục các dịch vụ cùng doanh thu của mỗi dịch vụ trong KTX trong mỗi tháng.
Các ứng dụng kiểm tra các ràng buộc về số người ở trong phòng, số xe tháng tối đa của mỗi sinh viên được đăng ký,… cần phải được thể hiện.