# ScoShow - Enhanced Multi-Monitor Support

## Phiên bản hiện có:

### 1. scoshow.py (Tkinter - Original)
- **Launcher**: `run_scoshow.bat`
- **Ưu điểm**: 
  - Nhẹ, ít dependencies
  - Giao diện quen thuộc
- **Nhược điểm**: 
  - Fullscreen có thể không hoạt động tốt trên multi-monitor
  - Hạn chế trong việc kiểm soát vị trí cửa sổ chính xác

### 2. scoshow_pyqt.py (PyQt5 - Enhanced)
- **Launcher**: `run_scoshow_pyqt.bat`
- **Ưu điểm**:
  - ✅ **Fullscreen tốt hơn trên nhiều màn hình**
  - ✅ **Kiểm soát chính xác màn hình hiển thị**
  - ✅ **Giao diện hiện đại và responsive**
  - ✅ **Ổn định hơn khi chuyển đổi giữa các màn hình**
- **Nhược điểm**:
  - Cần cài đặt PyQt5 (đã được cài đặt sẵn)
  - File size lớn hơn một chút

## Cách sử dụng:

### Chạy phiên bản PyQt (Khuyến nghị):
```bash
# Cách 1: Sử dụng launcher
run_scoshow_pyqt.bat

# Cách 2: Chạy trực tiếp
B:/Python/Projects/ScoShow/venv/Scripts/python.exe scoshow_pyqt.py
```

### Chạy phiên bản Tkinter (Backup):
```bash
# Cách 1: Sử dụng launcher
run_scoshow.bat

# Cách 2: Chạy trực tiếp
B:/Python/Projects/ScoShow/venv/Scripts/python.exe scoshow.py
```

## Tính năng nâng cao của phiên bản PyQt:

### 1. Multi-Monitor Fullscreen:
- Chọn màn hình hiển thị từ dropdown
- Fullscreen chính xác trên màn hình được chọn
- Không bị chuyển về màn hình chính khi fullscreen

### 2. Drag and Drop:
- Kéo cửa sổ display đến màn hình bất kỳ
- F11 để fullscreen ngay tại màn hình hiện tại
- ESC để thoát fullscreen và trở về vị trí cũ

### 3. Giao diện cải tiến:
- Layout hiện đại với PyQt5
- Responsive design
- Status indicators rõ ràng
- Keyboard shortcuts hoạt động tốt hơn

### 4. Debug Information:
- Ctrl+D để xem thông tin debug
- Hiển thị chính xác màn hình hiện tại
- Thông tin vị trí và kích thước cửa sổ

## Khuyến nghị:

**Sử dụng phiên bản PyQt** (`scoshow_pyqt.py`) cho:
- ✅ Presentations chuyên nghiệp
- ✅ Setup nhiều màn hình
- ✅ Cần kiểm soát chính xác fullscreen

**Sử dụng phiên bản Tkinter** (`scoshow.py`) cho:
- 📋 Testing nhanh
- 📋 Máy tính có hạn chế về resources
- 📋 Backup khi có vấn đề với PyQt

## Dependencies:

### Phiên bản PyQt:
```bash
PyQt5==5.15.11
PyQt5-Qt5==5.15.2
PyQt5-sip==12.17.0
Pillow
screeninfo
```

### Phiên bản Tkinter:
```bash
Pillow
screeninfo
tkinter (built-in)
```

## Branch Information:

- `main`: Phiên bản Tkinter ổn định
- `screen-drag`: Phiên bản Tkinter với drag & drop support  
- `Screen-switch`: Phiên bản PyQt với enhanced multi-monitor support (nhánh hiện tại)

---

**Tác giả**: Tournament Display System  
**Phiên bản**: 2.0 PyQt Enhanced  
**Ngày cập nhật**: {{ current_date }}
