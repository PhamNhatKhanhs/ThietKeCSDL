from app import create_app

# Tạo instance của ứng dụng Flask sử dụng factory function
app = create_app()

if __name__ == '__main__':
    # Chạy ứng dụng ở chế độ debug (chỉ dùng cho phát triển)
    # host='0.0.0.0' để có thể truy cập từ máy khác trong mạng (hoặc từ Windows vào WSL)
    app.run(host='0.0.0.0', port=5000, debug=True)