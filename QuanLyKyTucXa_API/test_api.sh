curl -X POST -H "Content-Type: application/json" -d \
'{
    "maKhach": 1,
    "maSV": "SV002",
    "ghiChu": "Bạn cùng lớp đến thăm"
}' \
http://localhost:5000/api/khach/tham
