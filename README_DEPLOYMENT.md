# ScoShow MQTT Remote Control - Deployment Guide

## 📦 Package Contents

- **ScoShow_Client.exe**: Ứng dụng hiển thị (chạy trên máy có màn hình lớn/projector)
- **ScoShow_Client_Debug.exe**: Ứng dụng hiển thị với console debug (để kiểm tra kết nối MQTT)
- **ScoShow_Remote.exe**: Ứng dụng điều khiển từ xa (phiên bản cơ bản)
- **ScoShow_Remote_Enhanced.exe**: Ứng dụng điều khiển từ xa (phiên bản cải tiến - KHUYÊN DÙNG)
- **mqtt_session.json**: File chứa Session ID chung cho cả 2 ứng dụng
- **background/**: Thư mục chứa background images
- **README_DEPLOYMENT.md**: File hướng dẫn này
- **README_ENHANCEMENTS.md**: Hướng dẫn các tính năng mới trong phiên bản Enhanced

## 🚀 Quick Start

### **Bước 1: Setup máy Client (Máy hiển thị)**
1. Copy `ScoShow_Client.exe` (hoặc `ScoShow_Client_Debug.exe` để debug), `mqtt_session.json` và thư mục `background/` vào máy hiển thị
2. **Để debug kết nối MQTT**: Chạy `ScoShow_Client_Debug.exe` (sẽ hiện cửa sổ console với thông tin debug)
3. **Chạy bình thường**: Chạy `ScoShow_Client.exe` (chạy ngầm trong system tray)
4. Ứng dụng sẽ tự động kết nối MQTT và sẵn sàng nhận lệnh

### **Bước 2: Setup máy Remote (Máy điều khiển)**
1. Copy `ScoShow_Remote_Enhanced.exe` (khuyên dùng) hoặc `ScoShow_Remote.exe` và `mqtt_session.json` vào máy điều khiển  
2. Chạy `ScoShow_Remote_Enhanced.exe` (hoặc `ScoShow_Remote.exe`)
3. Cửa sổ Remote Control sẽ xuất hiện

**📝 Lưu ý**: Khuyên dùng `ScoShow_Remote_Enhanced.exe` vì có nhiều tính năng cải tiến như tự động phát hiện màn hình, nhớ cài đặt, và tự động hiển thị WAIT(00) khi mở display.

### **Bước 3: Kết nối và sử dụng**
1. Trong Remote Control, kiểm tra **Connection Status**:
   - **MQTT: Connected** (màu xanh)
   - **Client: Online** (sau vài giây)
   
2. **Mở cửa sổ hiển thị**:
   - Tab "📺 Display Control"
   - Nhấn "📁 Browse" → chọn thư mục `background`
   - Nhấn "🚀 Open Display"
   
3. **Điều khiển hiển thị**:
   - **Background**: Nhấn "⏸️ Wait", "📊 Ranking", "🏆 Final"
   - **Ranking**: Tab "📊 Ranking" → nhập tên → "✅ Apply Ranking"
   - **Final Results**: Tab "🏆 Final Results" → nhập tên → "🏆 Apply Final Results"

## 🌐 Network Requirements

- **Internet connection** trên cả 2 máy (để kết nối MQTT broker công cộng)
- **Port 1883** không bị firewall chặn
- Máy có thể ở **khác mạng LAN** (chỉ cần có internet)

## 🔧 Troubleshooting

### **🐛 Debug MQTT Connection**
1. **Chạy phiên bản debug**: Sử dụng `ScoShow_Client_Debug.exe` thay vì `ScoShow_Client.exe`
2. **Cửa sổ console** sẽ hiển thị:
   - `🔄 Attempting to connect to MQTT broker...` → Đang kết nối
   - `🆔 Session ID: [session_id]` → Session ID đang sử dụng
   - `✅ Successfully connected to MQTT broker!` → Kết nối thành công  
   - `📥 Subscribing to MQTT topics...` → Đang đăng ký nhận lệnh
   - `💓 Heartbeat sent` → Đang gửi tín hiệu sống
   - `📨 Received message` → Nhận được lệnh từ Remote
3. **Nếu không kết nối được** sẽ hiển thị lỗi chi tiết và mã lỗi
4. **Kiểm tra Session ID**: Đảm bảo cả Client và Remote sử dụng cùng Session ID

### **⚠️ Session ID không khớp**
1. **Triệu chứng**: Remote báo "MQTT: Connected" nhưng "Client: Unknown"
2. **Nguyên nhân**: Client và Remote sử dụng khác Session ID
3. **Giải pháp**: 
   - Đảm bảo file `mqtt_session.json` có ở cả 2 máy
   - Restart cả 2 ứng dụng
   - Kiểm tra Session ID trong debug console

### **MQTT không kết nối được**
1. Kiểm tra internet connection
2. Kiểm tra firewall không chặn port 1883
3. Thử restart cả 2 ứng dụng
4. **Chạy debug version** để xem chi tiết lỗi

### **Client không nhận lệnh**
1. Kiểm tra cả 2 máy đều "Connected" trong Remote Control
2. Đảm bảo Client đang chạy và hiển thị heartbeat
3. Thử nhấn "🔄 Reconnect" trong Remote Control

### **Cửa sổ hiển thị không mở**
1. Đảm bảo đã chọn đúng thư mục background
2. Kiểm tra thư mục background có các file ảnh (00.jpg, 01.png, 02.png)
3. Thử nhấn "🖥️ Toggle Fullscreen" để chuyển chế độ hiển thị

## 📁 File Structure
```
ScoShow_Deployment/
├── ScoShow_Client.exe              # Client bình thường (chạy ngầm)
├── ScoShow_Client_Debug.exe        # Client với console debug
├── ScoShow_Remote.exe              # Remote control (phiên bản cơ bản)
├── ScoShow_Remote_Enhanced.exe     # Remote control (phiên bản cải tiến)
├── mqtt_session.json              # Session ID chung (QUAN TRỌNG!)
├── background/
│   ├── 00.jpg                      # Wait screen
│   ├── 01.png                      # Ranking screen
│   └── 02.png                      # Final results screen
├── README_DEPLOYMENT.md            # Hướng dẫn deployment
└── README_ENHANCEMENTS.md          # Hướng dẫn tính năng mới Enhanced
```

## 🎯 Usage Tips

1. **Khởi động thứ tự**: Client trước, Remote sau
2. **Debug**: Dùng `ScoShow_Client_Debug.exe` để xem log kết nối MQTT và Session ID
3. **Session file**: File `mqtt_session.json` phải có ở cả 2 máy để giao tiếp được
4. **Multi-monitor**: Client tự động phát hiện màn hình phụ
5. **Fullscreen**: Nhấn ESC để thoát fullscreen trên Client
6. **Session unique**: Mỗi lần restart tạo session ID mới (tránh xung đột)
7. **Console log**: Debug version hiển thị tất cả hoạt động MQTT

## 🔐 Security Note

- Sử dụng MQTT broker công cộng với unique session ID từ file `mqtt_session.json`
- Không có thông tin nhạy cảm được truyền
- Session ID được lưu trong file để đồng bộ giữa Client và Remote
- Nếu muốn tạo session mới, xóa file `mqtt_session.json` và restart ứng dụng
