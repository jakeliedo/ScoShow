# ScoShow - Slideshow Application

Ứng dụng trình chiếu slide đơn giản với khả năng hiển thị trên màn hình mở rộng và điều khiển từ màn hình chính.

## Tính năng

- **Slideshow fullscreen**: Hiển thị ảnh full màn hình trên màn hình mở rộng (extended display)
- **Panel điều khiển**: Cửa sổ điều khiển riêng biệt trên màn hình chính
- **Import ảnh linh hoạt**: 
  - Chọn thư mục chứa ảnh
  - Thêm từng ảnh riêng lẻ
  - Quản lý danh sách ảnh (thêm, xóa)
- **Điều khiển slideshow**:
  - Phát/dừng slideshow tự động
  - Chuyển ảnh thủ công (tiến/lùi)
  - Thiết lập thời gian giữa các slide
  - Hiển thị ảnh cụ thể từ danh sách
- **Hỗ trợ đa định dạng**: PNG, JPG, JPEG, GIF, BMP, TIFF

## Yêu cầu hệ thống

- Python 3.7+
- Windows/Linux/macOS
- Màn hình mở rộng (tùy chọn)

## Cài đặt

1. Clone hoặc download project về máy
2. Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

## Sử dụng

1. Chạy ứng dụng:

```bash
python scoshow.py
```

2. Sử dụng panel điều khiển:
   - **Chọn thư mục ảnh**: Import tất cả ảnh từ một thư mục
   - **Thêm ảnh**: Chọn từng ảnh riêng lẻ
   - **Mở Slideshow**: Mở cửa sổ slideshow trên màn hình mở rộng
   - **Điều khiển**: Sử dụng các nút phát/dừng, tiến/lùi để điều khiển slideshow

## Cấu trúc Project

```
ScoShow/
├── scoshow.py          # File chính của ứng dụng
├── requirements.txt    # Danh sách thư viện cần thiết
└── README.md          # Hướng dẫn sử dụng
```

## Các thư viện sử dụng

- **tkinter**: Giao diện người dùng (built-in Python)
- **Pillow**: Xử lý ảnh
- **screeninfo**: Phát hiện và quản lý màn hình

## Tính năng nâng cao

### Phát hiện màn hình tự động
- Ứng dụng tự động phát hiện số lượng màn hình
- Slideshow sẽ hiển thị trên màn hình thứ 2 nếu có
- Nếu chỉ có 1 màn hình, slideshow hiển thị trong cửa sổ

### Slideshow tự động
- Thiết lập thời gian giữa các slide (1-60 giây)
- Chạy trong thread riêng biệt để không block giao diện
- Có thể dừng và tiếp tục bất cứ lúc nào

### Quản lý ảnh
- Hiển thị danh sách ảnh đã import
- Xóa ảnh không cần thiết
- Hiển thị trực tiếp ảnh được chọn

## Phím tắt

- **Escape**: Thoát chế độ fullscreen trong slideshow

## Lưu ý

- Ảnh sẽ được tự động resize để vừa với màn hình mà vẫn giữ nguyên tỷ lệ
- Slideshow hỗ trợ hiển thị trên màn hình có độ phân giải khác nhau
- Ứng dụng sử dụng giao diện Tkinter nên có thể chạy trên mọi hệ điều hành có Python

## Troubleshooting

1. **Lỗi import thư viện**: Đảm bảo đã cài đặt đầy đủ requirements.txt
2. **Không phát hiện màn hình mở rộng**: Kiểm tra cài đặt hiển thị của hệ điều hành
3. **Ảnh không hiển thị**: Kiểm tra định dạng file ảnh có được hỗ trợ không

## Phát triển thêm

Có thể mở rộng thêm các tính năng:
- Hiệu ứng chuyển slide
- Zoom ảnh
- Slideshow với nhạc nền
- Lưu/load playlist ảnh
- Điều khiển từ xa qua mạng
