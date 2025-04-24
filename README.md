# 🏢 Dormitory Management System API

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/en/2.0.x/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-latest-red)](https://redis.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A comprehensive RESTful API backend system for managing student dormitory operations, including student information, room management, contracts, services, vehicle parking, visitor tracking, and billing.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Database Design](#database-design)
- [API Endpoints](#api-endpoints)
- [Installation Guide](#installation-guide)
  - [Prerequisites](#prerequisites)
  - [Setup Steps](#setup-steps)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Requirements](#project-requirements)

## 📝 Overview

This application provides RESTful API endpoints to perform CRUD operations on key data entities while implementing complex business logic related to dormitory management. The system integrates Redis for caching frequently accessed data, significantly improving read performance. Business rule validations (such as room occupancy limits and student vehicle registration constraints) are implemented at the service layer of the application.

## ✨ Key Features

- **Student Management**: Complete CRUD operations for student records
- **Room Types & Rooms Management**: Configurable room types with pricing and capacity constraints
- **Rental Contract Management**: Contract creation with room availability validation
- **Service Management**: Configurable service types and service usage tracking
- **Vehicle Registration System**: Monthly parking registration with usage monitoring
- **Vehicle Entry/Exit Tracking**: Automated fee calculation based on usage policy
- **Visitor Management**: Visitor registration and tracking
- **Billing System**: Automated monthly invoice generation and payment tracking
- **Advanced Reporting**: Complex query APIs for business intelligence
- **Performance Optimization**: Redis caching for GET operations

## 🛠️ Technology Stack

- **Backend**: Python 3.8+ with Flask framework
- **Database**: MySQL 8.0+
- **Caching**: Redis
- **Key Dependencies**:
  - `Flask`: Web framework
  - `mysql-connector-python`: MySQL database connector
  - `redis`: Redis client for caching
  - `python-dotenv`: Environment variable management
  - `flask-cors`: Cross-Origin Resource Sharing support
  - `marshmallow`: Object serialization/deserialization
  - `gunicorn`: WSGI HTTP Server (for production)

## 🗄️ Database Design

The system uses a relational database with the following entity structure:

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
```

### Database Setup Script

The file `QuanLyKyTucXa_Setup.sql` in this repository contains all the necessary SQL commands to:

- Create the `QuanLyKyTucXa` database
- Create all tables with primary keys, foreign keys, and constraint definitions
- Insert sample data for testing purposes
- Include complex SQL queries for reporting requirements (with clear comments)

## 🔌 API Endpoints

The application exposes the following RESTful API endpoints with the prefix `/api`:

### Student Management
- `GET /api/sinhvien`: Get all students
- `GET /api/sinhvien/{maSV}`: Get student by ID
- `POST /api/sinhvien`: Create new student
- `PUT /api/sinhvien/{maSV}`: Update student
- `DELETE /api/sinhvien/{maSV}`: Delete student

### Room Type Management
- `GET /api/loaiphong`: Get all room types
- `GET /api/loaiphong/{maLoaiPhong}`: Get room type by ID
- `POST /api/loaiphong`: Create new room type
- `PUT /api/loaiphong/{maLoaiPhong}`: Update room type
- `DELETE /api/loaiphong/{maLoaiPhong}`: Delete room type

### Room Management
- `GET /api/phong`: Get all rooms
- `GET /api/phong/{maPhong}`: Get room by ID
- `POST /api/phong`: Create new room
- `PUT /api/phong/{maPhong}`: Update room
- `DELETE /api/phong/{maPhong}`: Delete room

### Contract Management
- `GET /api/hopdong`: Get all contracts
- `GET /api/hopdong/sinhvien/{maSV}`: Get contracts by student ID
- `POST /api/hopdong`: Create new contract
- `PUT /api/hopdong/{maHopDong}`: Update contract status

### Service Type Management
- `GET /api/dichvu/loai`: Get all service types
- `GET /api/dichvu/loai/{maLoaiDV}`: Get service type by ID
- `POST /api/dichvu/loai`: Create new service type
- `PUT /api/dichvu/loai/{maLoaiDV}`: Update service type
- `DELETE /api/dichvu/loai/{maLoaiDV}`: Delete service type

### Service Management
- `GET /api/dichvu`: Get all services
- `GET /api/dichvu/{maDV}`: Get service by ID
- `POST /api/dichvu`: Create new service
- `PUT /api/dichvu/{maDV}`: Update service
- `DELETE /api/dichvu/{maDV}`: Delete service

### Service Usage Management
- `GET /api/dichvu/sudung/sinhvien/{maSV}`: Get service usage history by student
- `POST /api/dichvu/sudung`: Record service usage

### Vehicle Management
- `GET /api/guixe/xe`: Get all vehicles
- `GET /api/guixe/xe/sinhvien/{maSV}`: Get vehicles by student ID
- `POST /api/guixe/xe`: Register new vehicle
- `PUT /api/guixe/xe/{bienSoXe}`: Update vehicle information
- `DELETE /api/guixe/xe/{bienSoXe}`: Delete vehicle

### Monthly Vehicle Registration
- `GET /api/guixe/dangky`: Get all monthly registrations
- `GET /api/guixe/dangky/sinhvien/{maSV}`: Get registrations by student ID
- `POST /api/guixe/dangky`: Create new monthly registration
- `PUT /api/guixe/dangky/{maDangKy}`: Update registration
- `DELETE /api/guixe/dangky/{maDangKy}`: Cancel registration

### Vehicle Entry/Exit Management
- `GET /api/guixe/luot/dangky/{maDangKy}`: Get entry/exit logs by registration ID
- `POST /api/guixe/luot`: Record vehicle entry/exit

### Visitor Management
- `GET /api/khach`: Get all visitors
- `GET /api/khach/{maKhach}`: Get visitor by ID
- `GET /api/khach/cmt/{soCMT}`: Find visitor by ID card number
- `POST /api/khach`: Register new visitor
- `PUT /api/khach/{maKhach}`: Update visitor information

### Visitor Tracking
- `GET /api/khach/tham/sinhvien/{maSV}`: Get visitor logs by student ID
- `POST /api/khach/tham`: Record visitor entry
- `PUT /api/khach/tham/{maTham}`: Record visitor exit

### Billing Management
- `GET /api/hoadon`: Get all invoices
- `GET /api/hoadon/{maHoaDon}`: Get invoice details
- `GET /api/hoadon/sinhvien/{maSV}`: Get invoices by student ID
- `POST /api/hoadon/generate`: Trigger monthly invoice generation
- `PUT /api/hoadon/{maHoaDon}/pay`: Mark invoice as paid

### Reporting APIs
- `GET /api/bao-cao/chiphi-sinhvien`: Student expenses report
- `GET /api/bao-cao/sudung-dichvu`: Service usage report
- `GET /api/bao-cao/khach-tham`: Visitor statistics report
- `GET /api/bao-cao/doanhthu-dichvu`: Service revenue report

For detailed information on request parameters and response formats, refer to the source code in the `app/routes/` directory.

## 🚀 Installation Guide

### Prerequisites

- Python 3.8 or higher
- pip and venv (typically included with Python)
- MySQL Server 8.0+ running
- Redis Server running

### Setup Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/dormitory-management-api.git
   cd dormitory-management-api
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv venv

   # On Linux/macOS/WSL:
   source venv/bin/activate

   # On Windows (Command Prompt):
   venv\Scripts\activate.bat

   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Database**:
   - Ensure MySQL Server is running
   - Create a dedicated user and database (recommended) or use root account (for development only)
   - Run the SQL script to create tables and insert sample data:
   ```bash
   # Using root (development only):
   mysql -u root -p < QuanLyKyTucXa_Setup.sql

   # Using dedicated user:
   mysql -u your_username -p your_database < QuanLyKyTucXa_Setup.sql
   ```

## ⚙️ Configuration

1. **Create Environment Variables File**:
   Create a `.env` file in the project root directory with the following content:

   ```ini
   # Database Configuration
   MYSQL_HOST=localhost
   MYSQL_USER=your_mysql_username
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB=QuanLyKyTucXa

   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0

   # Flask Configuration
   FLASK_SECRET_KEY=your_secure_random_secret_key
   FLASK_ENV=development  # Change to 'production' for deployment
   ```

   **Important**: Replace the placeholder values with your actual configuration.

## 🏃‍♂️ Running the Application

1. **Start Redis Server** (if not already running):
   ```bash
   # On Linux:
   sudo systemctl start redis-server

   # On macOS with Homebrew:
   brew services start redis

   # On Windows:
   # Start Redis via Windows Service or WSL
   ```

2. **Run the Application**:
   ```bash
   # Development mode:
   python run.py

   # Production mode (using Gunicorn):
   gunicorn --workers=4 --bind 0.0.0.0:5000 "app:create_app()"
   ```

   The API will be available at `http://localhost:5000`.

## 🧪 Testing

You can test the API using one of the following methods:

1. **Automated Test Script**:
   ```bash
   chmod +x test_api.sh
   ./test_api.sh
   ```

2. **Using API Testing Tools**:
   - [Postman](https://www.postman.com/)
   - [Insomnia](https://insomnia.rest/)
   - [curl](https://curl.se/) for command-line testing

3. **Sample curl Commands**:
   ```bash
   # Get all students
   curl -X GET http://localhost:5000/api/sinhvien

   # Create a new student
   curl -X POST http://localhost:5000/api/sinhvien \
     -H "Content-Type: application/json" \
     -d '{"maSV": "SV001", "hoTen": "Nguyen Van A", "soCMT": "123456789", "ngaySinh": "2000-01-01", "lop": "K65-CNTT", "queQuan": "Ha Noi"}'
   ```

## 📄 Project Requirements

This project was developed as part of Project 2, meeting the following requirements:

1. Design and implement a database system for a student dormitory management application
2. Create sample data and implement complex SQL queries for reporting
3. Develop a comprehensive API for all CRUD operations and business requirements
4. Implement business logic validation for room occupancy, vehicle registration limits, etc.
5. Create specialized APIs for the following reporting needs:
   - Student expense reports (room and services)
   - Service usage reports by date range
   - Visitor tracking statistics
   - Service revenue reports

For the complete project requirements, please refer to the original project specification document.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Contributors

- Your Name - Initial work - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Project supervisor and instructors for their guidance
- Open-source community for providing the tools and libraries used in this project