# ScoShow Debug Features

## Tổng quan
File `scoshow_remote_enhanced.py` đã được nâng cấp với các tính năng debug chi tiết để theo dõi giao tiếp MQTT giữa Remote và Client.

## Các tính năng debug đã thêm

### 1. Debug logging system
- **Timestamp với millisecond**: Mỗi message đều có timestamp chính xác đến millisecond
- **Console và file logging**: Sử dụng Python logging module cho output có cấu trúc
- **Color-coded messages**: Sử dụng emoji để dễ phân biệt loại message

### 2. MQTT Connection Debug
```
🔌 Attempting to connect to MQTT broker: test.mosquitto.org:1883
📡 Session ID: xw12u4c1
📋 Topics to subscribe:
   - Status: scoshow_xw12u4c1/status
   - Heartbeat: scoshow_xw12u4c1/heartbeat
✅ Connected to MQTT broker successfully!
🎯 Remote is now ready to receive messages from client!
```

### 3. Message Reception Debug
Khi nhận được message từ client, hệ thống sẽ hiển thị:

#### Status Messages
```
============================================================
📨 RECEIVED MESSAGE FROM CLIENT
   Topic: scoshow_xw12u4c1/status
   Raw Payload: {"status": "online", "message": "Client connected and ready", "timestamp": 1754878233.9443822}
   Parsed Data: {
     "status": "online",
     "message": "Client connected and ready", 
     "timestamp": 1754878233.9443822
   }
📊 Processing STATUS message...
   Status: online
   Message: Client connected and ready
   Timestamp: 1754878233.9443822
============================================================
🎯 CLIENT STATUS UPDATE RECEIVED:
   Status: online
   Message: Client connected and ready
   Timestamp: 1754878233.9443822
   Time: 09:10:33
✅ Client is ONLINE and ready!
```

#### Heartbeat Messages
```
============================================================
📨 RECEIVED MESSAGE FROM CLIENT
   Topic: scoshow_xw12u4c1/heartbeat
   Raw Payload: {"timestamp": 1754878242.0692801, "client_id": "scoshow_client"}
   Parsed Data: {
     "timestamp": 1754878242.0692801,
     "client_id": "scoshow_client"
   }
💓 Processing HEARTBEAT message...
   Client alive at: 1754878242.0692801
   Display status: unknown
   Background: unknown
============================================================
💓 CLIENT HEARTBEAT RECEIVED:
   Timestamp: 1754878242.0692801
   Time: 09:10:42
💓 Heartbeat processed successfully
```

### 4. Command Sending Debug
Khi gửi lệnh đến client:
```
📤 SENDING COMMAND TO CLIENT
   Command Type: commands
   Topic: scoshow_xw12u4c1/commands
   Data: {
     "action": "open_display",
     "monitor_index": 0,
     "background_folder": "/path/to/background"
   }
✅ Command sent successfully!
```

### 5. Connection Status Debug
```
🟢 MQTT Connection established!  # Khi kết nối thành công
🔴 MQTT Connection lost!         # Khi mất kết nối
```

### 6. Error Handling Debug
```
❌ Error processing message: [error details]
   Topic: [topic name]
   Raw payload: [raw data]
❌ Cannot send command - MQTT not connected!
❌ Failed to send command, RC: [return code]
```

### 7. Client Status Monitoring
```
✅ Client is ONLINE and ready!
❌ Client reported an ERROR!
⚠️ CLIENT TIMEOUT! Last heartbeat was 65.3 seconds ago
⚠️ No heartbeat received yet from client
```

## Cách sử dụng Debug Version

### 1. Chạy Remote Enhanced với Debug
```bash
python scoshow_remote_enhanced.py
```

### 2. Chạy Client Debug
```bash  
python scoshow_client_debug.py
```

### 3. Theo dõi console output
- Remote sẽ hiển thị tất cả message nhận được từ client
- Bao gồm status updates, heartbeat, và error messages
- Timestamp chính xác cho mỗi sự kiện

## Thông tin Debug chi tiết

### MQTT Topics được monitor
- `scoshow_[session_id]/status` - Trạng thái client
- `scoshow_[session_id]/heartbeat` - Heartbeat từ client
- `scoshow_[session_id]/commands` - Lệnh gửi đến client  
- `scoshow_[session_id]/ranking` - Cập nhật ranking
- `scoshow_[session_id]/final` - Kết quả chung cuộc
- `scoshow_[session_id]/display` - Điều khiển hiển thị
- `scoshow_[session_id]/background` - Cài đặt background

### Status Types nhận được từ Client
- `online` - Client đã kết nối và sẵn sàng
- `error` - Client gặp lỗi
- `display_opened` - Đã mở display
- `display_closed` - Đã đóng display
- `background_changed` - Đã đổi background
- `ranking_applied` - Đã áp dụng ranking
- `final_applied` - Đã áp dụng kết quả chung cuộc

### Heartbeat Information
- `timestamp` - Thời gian heartbeat
- `client_id` - ID của client
- `display_status` - Trạng thái display (nếu có)
- `current_background` - Background hiện tại (nếu có)
- `system_info` - Thông tin hệ thống (nếu có)
- `client_version` - Version của client (nếu có)
- `uptime` - Thời gian chạy của client (nếu có)

## Troubleshooting với Debug

### 1. Không nhận được message từ client
- Kiểm tra session ID giống nhau
- Kiểm tra MQTT broker connection
- Kiểm tra topic subscription

### 2. Message bị lỗi format
- Debug sẽ hiển thị raw payload
- Kiểm tra JSON format
- Kiểm tra encoding

### 3. Connection issues
- Debug hiển thị return code khi connect
- Hiển thị authentication status
- Hiển thị broker address và port

## Performance Impact

Debug logging có thể ảnh hưởng nhẹ đến performance:
- Console output sẽ chậm hơn
- File logging tăng I/O
- Memory usage tăng do string formatting

Để tắt debug trong production, có thể comment out các dòng `debug_print()` hoặc thay đổi logging level.

## Sample Debug Session

```
🚀 Starting ScoShow Remote Control (Enhanced Debug Version)
[09:10:12.783] 🚀 ScoShow Remote Control starting...
[09:10:12.938] 🔌 Attempting to connect to MQTT broker: test.mosquitto.org:1883
[09:10:13.672] ✅ Connected to MQTT broker successfully!
[09:10:13.673] 🎯 Remote is now ready to receive messages from client!
[09:10:34.631] 📨 RECEIVED MESSAGE FROM CLIENT
[09:10:34.634] ✅ Client is ONLINE and ready!
[09:10:42.408] 💓 CLIENT HEARTBEAT RECEIVED:
[09:10:42.408] 💓 Heartbeat processed successfully
```

Debug version giúp dễ dàng troubleshoot và monitor hoạt động của hệ thống MQTT remote control.
