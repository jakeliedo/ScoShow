"""
ScoShow - Tournament Ranking Display (PyQt Version)
Ứng dụng hiển thị bảng xếp hạng tournament trên màn hình mở rộng với điều khiển từ màn hình chính
"""

import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QComboBox, QGroupBox, QGridLayout, QScrollArea,
                             QFileDialog, QMessageBox, QTabWidget, QFrame,
                             QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QRect
from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QKeySequence, QIcon
from PIL import Image, ImageDraw, ImageFont
import threading
import time
from screeninfo import get_monitors

class TournamentDisplayWindow(QMainWindow):
    """Cửa sổ hiển thị tournament trên màn hình mở rộng với PyQt"""
    
    def __init__(self, monitor_index=1):
        super().__init__()
        self.monitor_index = monitor_index
        self.is_fullscreen = False
        self.stored_geometry = None
        
        # Thiết lập cửa sổ cơ bản
        self.setup_window()
        
        # Thiết lập giao diện
        self.setup_ui()
        
        # Thiết lập phím tắt
        self.setup_shortcuts()
        
        # Dữ liệu nền và overlay
        self.current_background = None
        self.background_paths = {}
        
        # Hiển thị hướng dẫn ban đầu
        self.show_instructions()
        
    def setup_window(self):
        """Thiết lập cửa sổ ban đầu"""
        self.setWindowTitle("ScoShow - Tournament Display (F11: Toggle Fullscreen, ESC: Exit Fullscreen)")
        self.setStyleSheet("background-color: black;")
        
        # Đặt cửa sổ trên màn hình được chọn
        self.position_on_monitor(self.monitor_index)
        
    def position_on_monitor(self, monitor_index):
        """Đặt cửa sổ trên màn hình được chỉ định"""
        monitors = get_monitors()
        
        if monitor_index < len(monitors):
            monitor = monitors[monitor_index]
            # Tạo cửa sổ với kích thước 80% màn hình
            width = int(monitor.width * 0.8)
            height = int(monitor.height * 0.8)
            x = monitor.x + (monitor.width - width) // 2
            y = monitor.y + (monitor.height - height) // 2
            
            self.setGeometry(x, y, width, height)
            print(f"Positioned window on Monitor {monitor_index + 1}: {width}x{height} at ({x},{y})")
        else:
            # Fallback nếu không có màn hình mở rộng
            self.setGeometry(100, 100, 800, 600)
            print("Using default window position")
            
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label để hiển thị hình ảnh
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label)
        
        # Label hướng dẫn (overlay)
        self.instruction_label = QLabel()
        self.instruction_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: yellow;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self.instruction_label.setWordWrap(True)
        self.instruction_label.hide()
        
        # Label debug info (overlay)
        self.debug_label = QLabel()
        self.debug_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 255, 180);
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        self.debug_label.setWordWrap(True)
        self.debug_label.hide()
        
        # Thêm labels overlay vào layout
        self.instruction_label.setParent(central_widget)
        self.debug_label.setParent(central_widget)
        
    def setup_shortcuts(self):
        """Thiết lập phím tắt"""
        # F11: Toggle fullscreen
        self.setShortcut(QKeySequence(Qt.Key_F11), self.toggle_fullscreen)
        
        # ESC: Exit fullscreen
        self.setShortcut(QKeySequence(Qt.Key_Escape), self.exit_fullscreen)
        
        # Ctrl+D: Debug info
        self.setShortcut(QKeySequence("Ctrl+D"), self.show_debug_info)
        
    def setShortcut(self, key_sequence, slot):
        """Helper để thiết lập phím tắt"""
        from PyQt5.QtWidgets import QShortcut
        shortcut = QShortcut(key_sequence, self)
        shortcut.activated.connect(slot)
        
    def resizeEvent(self, event):
        """Xử lý sự kiện thay đổi kích thước"""
        super().resizeEvent(event)
        
        # Cập nhật vị trí các overlay labels
        if hasattr(self, 'instruction_label'):
            self.instruction_label.move(10, 10)
            self.instruction_label.resize(400, 150)
            
        if hasattr(self, 'debug_label'):
            self.debug_label.move(10, 180)
            self.debug_label.resize(350, 120)
            
    def toggle_fullscreen(self):
        """Chuyển đổi chế độ fullscreen"""
        if not self.is_fullscreen:
            self.enter_fullscreen()
        else:
            self.exit_fullscreen()
            
    def enter_fullscreen(self):
        """Vào chế độ fullscreen trên màn hình hiện tại"""
        # Lưu geometry hiện tại
        self.stored_geometry = self.geometry()
        
        # Xác định màn hình hiện tại
        current_screen = QApplication.desktop().screenNumber(self)
        screen_geometry = QApplication.desktop().screenGeometry(current_screen)
        
        print(f"Entering fullscreen on screen {current_screen + 1}: {screen_geometry}")
        
        # Chuyển sang fullscreen
        self.showFullScreen()
        
        # Đặt cửa sổ đúng vị trí màn hình
        self.setGeometry(screen_geometry)
        
        self.is_fullscreen = True
        self.hide_instructions()
        
    def exit_fullscreen(self):
        """Thoát khỏi chế độ fullscreen"""
        if self.is_fullscreen:
            self.showNormal()
            
            # Khôi phục geometry đã lưu
            if self.stored_geometry:
                self.setGeometry(self.stored_geometry)
                print(f"Restored geometry: {self.stored_geometry}")
            
            self.is_fullscreen = False
            self.show_instructions()
            
    def show_instructions(self):
        """Hiển thị hướng dẫn sử dụng"""
        instructions = """🎯 HƯỚNG DẪN SỬ DỤNG:
• Kéo thả cửa sổ này đến màn hình mong muốn
• Nhấn F11 để bật/tắt fullscreen (giữ nguyên màn hình hiện tại)
• Nhấn ESC để thoát fullscreen
• Nhấn Ctrl+D để xem thông tin debug
• Fullscreen sẽ duy trì màn hình bạn đã chọn"""
        
        self.instruction_label.setText(instructions)
        self.instruction_label.show()
        
        # Tự động ẩn sau 5 giây
        QTimer.singleShot(5000, self.hide_instructions)
        
    def hide_instructions(self):
        """Ẩn hướng dẫn sử dụng"""
        self.instruction_label.hide()
        
    def show_debug_info(self):
        """Hiển thị thông tin debug"""
        current_screen = QApplication.desktop().screenNumber(self)
        screen_count = QApplication.desktop().screenCount()
        geometry = self.geometry()
        
        debug_text = f"""🖥️ THÔNG TIN DEBUG:
Vị trí cửa sổ: ({geometry.x()}, {geometry.y()})
Kích thước: {geometry.width()}x{geometry.height()}
Fullscreen: {'Có' if self.is_fullscreen else 'Không'}
Màn hình hiện tại: {current_screen + 1}
Tổng số màn hình: {screen_count}
Vị trí đã lưu: {self.stored_geometry if self.stored_geometry else 'Chưa có'}"""
        
        self.debug_label.setText(debug_text)
        self.debug_label.show()
        
        # Tự động ẩn sau 3 giây
        QTimer.singleShot(3000, self.debug_label.hide)
        
        print(debug_text.replace('🖥️ ', '').replace('\n', ', '))
        
    def load_background_folder(self, folder_path):
        """Tải thư mục chứa ảnh nền"""
        required_files = ["00.jpg", "01.png", "02.png"]
        found_files = {}
        
        for filename in required_files:
            full_path = os.path.join(folder_path, filename)
            if os.path.exists(full_path):
                bg_id = filename.split('.')[0]
                found_files[bg_id] = full_path
                
        if len(found_files) >= 3:
            self.background_paths = found_files
            return True
        return False
        
    def show_background(self, bg_id, overlay_data=None):
        """Hiển thị ảnh nền với overlay text"""
        if bg_id not in self.background_paths:
            return False

        try:
            # Mở ảnh nền
            background_path = self.background_paths[bg_id]
            image = Image.open(background_path).copy()

            # Thêm text overlay nếu có
            if overlay_data:
                self.add_text_overlay(image, bg_id, overlay_data)

            # Lấy kích thước màn hình hiện tại (màn hình mà cửa sổ đang hiển thị)
            current_screen = QApplication.desktop().screenNumber(self)
            screen_geometry = QApplication.desktop().screenGeometry(current_screen)
            screen_width = screen_geometry.width()

            # Tính toán chiều cao dựa trên tỷ lệ ảnh gốc
            original_aspect_ratio = image.width / image.height
            new_height = int(screen_width / original_aspect_ratio)

            # Resize ảnh để chiều ngang bằng màn hình, chiều cao theo tỷ lệ
            resized_image = image.resize((screen_width, new_height), Image.Resampling.LANCZOS)

            # Chuyển đổi PIL Image sang QPixmap
            image_rgb = resized_image.convert('RGB')
            qimg = self.pil_to_qpixmap(image_rgb)

            # Hiển thị ảnh với kích thước thực tế (không scale)
            self.image_label.setScaledContents(False)
            self.image_label.setPixmap(qimg)

            self.current_background = bg_id
            print(f"Image resized to: {screen_width}x{new_height} (aspect ratio: {original_aspect_ratio:.2f})")
            return True

        except Exception as e:
            print(f"Lỗi khi hiển thị ảnh nền {bg_id}: {e}")
            return False
            
    def pil_to_qpixmap(self, pil_image):
        """Chuyển đổi PIL Image sang QPixmap"""
        from PyQt5.QtGui import QImage
        
        # Chuyển đổi PIL image sang QImage
        rgb_image = pil_image.convert('RGB')
        w, h = rgb_image.size
        ch = 3
        bytes_per_line = ch * w
        
        qt_image = QImage(rgb_image.tobytes(), w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qt_image)
        
    def add_text_overlay(self, image, bg_id, overlay_data):
        """Thêm text overlay lên ảnh"""
        draw = ImageDraw.Draw(image)
        
        if bg_id == "01":  # Background cập nhật thứ hạng
            self.add_ranking_overlay(draw, overlay_data)
        elif bg_id == "02":  # Background kết quả cuối
            self.add_final_overlay(draw, overlay_data)
            
    def add_ranking_overlay(self, draw, data):
        """Thêm text ranking cho background 01"""
        # Lấy font settings
        font_settings = data.get('font_settings', {})
        font_name = font_settings.get('font_name', 'arial.ttf')
        rank_font_size = font_settings.get('rank_font_size', 60)
        round_font_size = font_settings.get('round_font_size', 60)
        color = font_settings.get('color', 'white')
        
        # Tạo font cho ranking và round
        try:
            rank_font = ImageFont.truetype(font_name, rank_font_size)
        except:
            try:
                rank_font = ImageFont.truetype(f"C:/Windows/Fonts/{font_name}", rank_font_size)
            except:
                rank_font = ImageFont.load_default()
                
        try:
            round_font = ImageFont.truetype(font_name, round_font_size)
        except:
            try:
                round_font = ImageFont.truetype(f"C:/Windows/Fonts/{font_name}", round_font_size)
            except:
                round_font = ImageFont.load_default()
        
        # Lấy vị trí từ data
        positions = data.get('positions', {})
        
        # Vẽ số round
        if 'round' in data and data['round'] and 'round' in positions:
            x, y = positions['round']
            draw.text((x, y), str(data['round']), fill=color, font=round_font)
            
        # Vẽ tên players cho các rank
        for rank in ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']:
            if rank in data and data[rank] and rank in positions and positions[rank]:
                x, y = positions[rank]
                draw.text((x, y), data[rank], fill=color, font=rank_font)
                
    def add_final_overlay(self, draw, data):
        """Thêm text kết quả cuối cho background 02"""
        # Lấy font settings
        font_settings = data.get('font_settings', {})
        font_name = font_settings.get('font_name', 'arial.ttf')
        font_size = font_settings.get('font_size', 60)
        color = font_settings.get('color', 'white')
        
        # Tạo font
        try:
            font = ImageFont.truetype(font_name, font_size)
        except:
            try:
                font = ImageFont.truetype(f"C:/Windows/Fonts/{font_name}", font_size)
            except:
                font = ImageFont.load_default()
        
        # Lấy vị trí từ data
        positions = data.get('positions', {})
        
        # Vẽ kết quả cuối
        for key in ['winner', 'second', 'third', 'fourth', 'fifth']:
            if key in data and data[key] and key in positions and positions[key]:
                x, y = positions[key]
                draw.text((x, y), data[key], fill=color, font=font)

class TournamentControlPanel(QMainWindow):
    """Panel điều khiển tournament trên màn hình chính với PyQt"""
    
    def __init__(self):
        super().__init__()
        
        # Khởi tạo biến
        self.display_window = None
        self.background_folder = ""
        self.current_mode = None
        self.selected_monitor = 0
        self.config_file = "scoshow_config.json"
        
        # Thiết lập cửa sổ
        self.setup_window()
        
        # Thiết lập biến input
        self.setup_variables()
        
        # Load config
        self.load_config()
        
        # Thiết lập giao diện
        self.setup_ui()
        
    def setup_window(self):
        """Thiết lập cửa sổ chính"""
        self.setWindowTitle("ScoShow - Tournament Control (PyQt Version)")
        self.setGeometry(100, 100, 1000, 900)
        self.setMinimumSize(960, 886)
        
        # Đặt cửa sổ ở giữa màn hình chính (monitor 0)
        desktop = QApplication.desktop()
        screen_geometry = desktop.screenGeometry(0)  # Màn hình chính
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
        
    def setup_variables(self):
        """Thiết lập biến cho các ô input"""
        # Variables cho background 01 (ranking)
        self.round_var = ""
        self.rank_vars = {
            '1st': '', '2nd': '', '3rd': '', '4th': '', '5th': '',
            '6th': '', '7th': '', '8th': '', '9th': '', '10th': ''
        }
        
        # Tọa độ cho round và ranking
        self.round_position = "1286,917"
        self.round_font_size = "60"
        self.rank_positions = {
            '1st': "1000,400", '2nd': "1000,500", '3rd': "1000,600", 
            '4th': "1000,700", '5th': "1000,800", '6th': "1000,900", 
            '7th': "1000,1000", '8th': "2000,400", '9th': "2000,500", 
            '10th': "2000,600"
        }
        
        # Font settings
        self.rank_font_size = "60"
        self.font_name = "arial.ttf"
        self.font_color = "white"
        
        # Variables cho background 02 (final results)
        self.final_vars = {
            'winner': '', 'second': '', 'third': '', 'fourth': '', 'fifth': ''
        }
        self.final_positions = {
            'winner': "1920,300", 'second': "1920,450", 'third': "1920,600",
            'fourth': "1920,750", 'fifth': "1920,900"
        }
        self.final_font_size = "60"
        
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Widget chính
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout chính với scroll
        main_layout = QVBoxLayout(central_widget)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Header
        self.create_header(scroll_layout)
        
        # Monitor setup
        self.create_monitor_section(scroll_layout)
        
        # Background setup
        self.create_background_section(scroll_layout)
        
        # Display controls
        self.create_display_controls(scroll_layout)
        
        # Ranking input (Background 01)
        self.create_ranking_section(scroll_layout)
        
        # Final results (Background 02)
        self.create_final_section(scroll_layout)
        
        # Status
        self.create_status_section(scroll_layout)
        
        # Thiết lập scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
    def create_header(self, layout):
        """Tạo header"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2C3E50;
                border-radius: 5px;
                margin: 5px;
            }
            QLabel {
                color: #ECF0F1;
                padding: 10px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        title = QLabel("🏆 ScoShow - Tournament Ranking (PyQt Version)")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Professional Tournament Display System - Enhanced Multi-Monitor Support")
        subtitle.setFont(QFont("Arial", 9, QFont.StyleItalic))
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_frame)
        
    def create_monitor_section(self, layout):
        """Tạo section chọn màn hình"""
        group = QGroupBox("🖥️ Monitor Setup")
        group_layout = QVBoxLayout(group)
        
        # Thông tin màn hình
        monitors = get_monitors()
        info_label = QLabel(f"📺 Detected {len(monitors)} monitor(s)")
        info_label.setFont(QFont("Arial", 9, QFont.Bold))
        info_label.setStyleSheet("color: #2980B9;")
        group_layout.addWidget(info_label)
        
        # Chọn màn hình
        monitor_layout = QHBoxLayout()
        monitor_layout.addWidget(QLabel("Display on Monitor:"))
        
        self.monitor_combo = QComboBox()
        for i, monitor in enumerate(monitors):
            self.monitor_combo.addItem(f"Monitor {i+1} ({monitor.width}x{monitor.height})")
        self.monitor_combo.setCurrentIndex(self.selected_monitor)
        monitor_layout.addWidget(self.monitor_combo)
        
        group_layout.addLayout(monitor_layout)
        
        # Status
        if len(monitors) > 1:
            status_text = "✅ Multiple monitors available - Choose monitor above"
            color = "#27AE60"
        else:
            status_text = "⚠️ Only 1 monitor - will display in window"
            color = "#F39C12"
            
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {color}; font-size: 10px;")
        group_layout.addWidget(status_label)
        
        layout.addWidget(group)
        
    def create_background_section(self, layout):
        """Tạo section chọn background"""
        group = QGroupBox("🖼️ Background Setup")
        group_layout = QHBoxLayout(group)
        
        bg_button = QPushButton("📁 Select Background Folder")
        bg_button.clicked.connect(self.select_background_folder)
        bg_button.setStyleSheet("""
            QPushButton {
                background-color: #2980B9;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3498DB;
            }
        """)
        group_layout.addWidget(bg_button)
        
        self.bg_status_label = QLabel("❌ No folder selected")
        self.bg_status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        group_layout.addWidget(self.bg_status_label)
        
        layout.addWidget(group)
        
    def create_display_controls(self, layout):
        """Tạo controls cho display"""
        group = QGroupBox("🎮 Display Control")
        group_layout = QVBoxLayout(group)
        
        # Nút điều khiển display
        display_layout = QHBoxLayout()
        
        open_btn = QPushButton("🚀 Open Display")
        open_btn.clicked.connect(self.open_display)
        open_btn.setStyleSheet(self.get_button_style("#229954"))
        display_layout.addWidget(open_btn)
        
        fullscreen_btn = QPushButton("🖥️ Toggle Fullscreen")
        fullscreen_btn.clicked.connect(self.toggle_display_fullscreen)
        fullscreen_btn.setStyleSheet(self.get_button_style("#2980B9"))
        display_layout.addWidget(fullscreen_btn)
        
        switch_btn = QPushButton("🔄 Switch Monitor")
        switch_btn.clicked.connect(self.switch_monitor)
        switch_btn.setStyleSheet(self.get_button_style("#2980B9"))
        display_layout.addWidget(switch_btn)
        
        close_btn = QPushButton("🔴 Close Display")
        close_btn.clicked.connect(self.close_display)
        close_btn.setStyleSheet(self.get_button_style("#E67E22"))
        display_layout.addWidget(close_btn)
        
        group_layout.addLayout(display_layout)
        
        # Nút chọn background
        bg_layout = QHBoxLayout()
        
        bg00_btn = QPushButton("⏸️ Show 00 (Waiting)")
        bg00_btn.clicked.connect(lambda: self.show_background("00"))
        bg00_btn.setStyleSheet(self.get_button_style("#2980B9"))
        bg_layout.addWidget(bg00_btn)
        
        bg01_btn = QPushButton("📊 Show 01 (Ranking)")
        bg01_btn.clicked.connect(lambda: self.show_background("01"))
        bg01_btn.setStyleSheet(self.get_button_style("#229954"))
        bg_layout.addWidget(bg01_btn)
        
        bg02_btn = QPushButton("🏆 Show 02 (Final)")
        bg02_btn.clicked.connect(lambda: self.show_background("02"))
        bg02_btn.setStyleSheet(self.get_button_style("#E67E22"))
        bg_layout.addWidget(bg02_btn)
        
        group_layout.addLayout(bg_layout)
        layout.addWidget(group)
        
    def get_button_style(self, color):
        """Lấy style cho button"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {color}DD;
            }}
        """
        
    def create_ranking_section(self, layout):
        """Tạo section input ranking"""
        group = QGroupBox("📊 Ranking Input (Background 01)")
        group_layout = QVBoxLayout(group)
        
        # Font settings
        font_frame = QFrame()
        font_frame.setStyleSheet("background-color: #F8F9FA; border-radius: 5px; padding: 5px;")
        font_layout = QHBoxLayout(font_frame)
        
        font_layout.addWidget(QLabel("🎨 Font:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["arial.ttf", "times.ttf", "calibri.ttf", "verdana.ttf"])
        font_layout.addWidget(self.font_combo)
        
        font_layout.addWidget(QLabel("Size:"))
        self.rank_font_size_edit = QLineEdit(self.rank_font_size)
        self.rank_font_size_edit.setMaximumWidth(50)
        font_layout.addWidget(self.rank_font_size_edit)
        
        font_layout.addWidget(QLabel("Color:"))
        self.font_color_combo = QComboBox()
        self.font_color_combo.addItems(["white", "black", "red", "blue", "green", "yellow"])
        font_layout.addWidget(self.font_color_combo)
        
        group_layout.addWidget(font_frame)
        
        # Round input
        round_frame = QFrame()
        round_frame.setStyleSheet("background-color: #E8F4FD; border-radius: 5px; padding: 5px;")
        round_layout = QHBoxLayout(round_frame)
        
        round_layout.addWidget(QLabel("🔄 Round:"))
        self.round_edit = QLineEdit()
        round_layout.addWidget(self.round_edit)
        
        round_layout.addWidget(QLabel("Position (x,y):"))
        self.round_pos_edit = QLineEdit(self.round_position)
        round_layout.addWidget(self.round_pos_edit)
        
        round_layout.addWidget(QLabel("Font Size:"))
        self.round_font_size_edit = QLineEdit(self.round_font_size)
        self.round_font_size_edit.setMaximumWidth(50)
        round_layout.addWidget(self.round_font_size_edit)
        
        group_layout.addWidget(round_frame)
        
        # Ranking inputs
        ranking_frame = QFrame()
        ranking_layout = QGridLayout(ranking_frame)
        
        self.rank_edits = {}
        self.rank_pos_edits = {}
        
        ranks = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
        for i, rank in enumerate(ranks):
            row = i % 5
            col = (i // 5) * 3
            
            ranking_layout.addWidget(QLabel(f"{rank}:"), row, col)
            
            self.rank_edits[rank] = QLineEdit()
            ranking_layout.addWidget(self.rank_edits[rank], row, col + 1)
            
            self.rank_pos_edits[rank] = QLineEdit(self.rank_positions[rank])
            self.rank_pos_edits[rank].setMaximumWidth(80)
            ranking_layout.addWidget(self.rank_pos_edits[rank], row, col + 2)
            
        group_layout.addWidget(ranking_frame)
        
        # Apply button
        apply_btn = QPushButton("✅ Apply Ranking")
        apply_btn.clicked.connect(self.apply_ranking)
        apply_btn.setStyleSheet(self.get_button_style("#229954"))
        group_layout.addWidget(apply_btn)
        
        layout.addWidget(group)
        
    def create_final_section(self, layout):
        """Tạo section final results"""
        group = QGroupBox("🏆 Final Results Input (Background 02)")
        group_layout = QVBoxLayout(group)
        
        # Font settings cho final
        final_font_frame = QFrame()
        final_font_frame.setStyleSheet("background-color: #FEF9E7; border-radius: 5px; padding: 5px;")
        final_font_layout = QHBoxLayout(final_font_frame)
        
        final_font_layout.addWidget(QLabel("🎨 Font:"))
        final_font_layout.addWidget(QLabel("(Uses same as ranking)"))
        
        final_font_layout.addWidget(QLabel("Size:"))
        self.final_font_size_edit = QLineEdit(self.final_font_size)
        self.final_font_size_edit.setMaximumWidth(50)
        final_font_layout.addWidget(self.final_font_size_edit)
        
        group_layout.addWidget(final_font_frame)
        
        # Final results inputs
        final_frame = QFrame()
        final_frame.setStyleSheet("background-color: #FDEDEC; border-radius: 5px; padding: 5px;")
        final_layout = QGridLayout(final_frame)
        
        self.final_edits = {}
        self.final_pos_edits = {}
        
        final_labels = {
            'winner': '🥇 1st Place:', 'second': '🥈 2nd Place:', 'third': '🥉 3rd Place:',
            'fourth': '🏅 4th Place:', 'fifth': '🎖️ 5th Place:'
        }
        
        for i, (key, label) in enumerate(final_labels.items()):
            final_layout.addWidget(QLabel(label), i, 0)
            
            self.final_edits[key] = QLineEdit()
            final_layout.addWidget(self.final_edits[key], i, 1)
            
            final_layout.addWidget(QLabel("Position:"), i, 2)
            self.final_pos_edits[key] = QLineEdit(self.final_positions[key])
            self.final_pos_edits[key].setMaximumWidth(100)
            final_layout.addWidget(self.final_pos_edits[key], i, 3)
            
        group_layout.addWidget(final_frame)
        
        # Apply button
        apply_final_btn = QPushButton("🏆 Apply Final Results")
        apply_final_btn.clicked.connect(self.apply_final_results)
        apply_final_btn.setStyleSheet(self.get_button_style("#E67E22"))
        group_layout.addWidget(apply_final_btn)
        
        layout.addWidget(group)
        
    def create_status_section(self, layout):
        """Tạo status section"""
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #E8F6F3; border-radius: 5px; padding: 10px;")
        status_layout = QVBoxLayout(status_frame)
        
        status_title = QLabel("📊 System Status")
        status_title.setFont(QFont("Arial", 9, QFont.Bold))
        status_title.setStyleSheet("color: #27AE60;")
        status_layout.addWidget(status_title)
        
        self.status_label = QLabel("Ready to start tournament display\n💡 Enhanced PyQt version with better multi-monitor fullscreen support")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_frame)
        
    def select_background_folder(self):
        """Chọn thư mục background"""
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục chứa background (00.jpg, 01.png, 02.png)")
        if folder:
            self.background_folder = folder
            required_files = ["00.jpg", "01.png", "02.png"]
            missing_files = [f for f in required_files if not os.path.exists(os.path.join(folder, f))]
            
            if missing_files:
                QMessageBox.warning(self, "Cảnh báo", f"Thiếu các file: {', '.join(missing_files)}")
                self.bg_status_label.setText("❌ Thiếu file background")
                self.bg_status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
            else:
                self.bg_status_label.setText("✅ Background OK")
                self.bg_status_label.setStyleSheet("color: #27AE60; font-weight: bold;")
                
    def open_display(self):
        """Mở cửa sổ hiển thị"""
        if not self.background_folder:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn thư mục background trước")
            return
            
        monitor_index = self.monitor_combo.currentIndex()
        
        # Đóng display cũ nếu có
        if self.display_window:
            self.display_window.close()
            
        # Tạo display mới
        self.display_window = TournamentDisplayWindow(monitor_index)
        
        if self.display_window.load_background_folder(self.background_folder):
            self.display_window.show()
            self.status_label.setText(f"Display opened on Monitor {monitor_index + 1}")
            
            # Khôi phục background đã chọn
            if self.current_mode:
                if self.current_mode == "00":
                    self.display_window.show_background("00")
                elif self.current_mode == "01":
                    self.apply_ranking(show_popup=False)
                elif self.current_mode == "02":
                    self.apply_final_results(show_popup=False)
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể load background")
            
    def close_display(self):
        """Đóng display"""
        if self.display_window:
            self.display_window.close()
            self.display_window = None
            self.status_label.setText("Display closed")
        else:
            QMessageBox.information(self, "Thông báo", "Không có display nào đang mở")
            
    def switch_monitor(self):
        """Chuyển monitor"""
        if self.display_window:
            self.open_display()  # Reopen trên monitor mới
        else:
            QMessageBox.warning(self, "Cảnh báo", "Không có display nào đang mở")
            
    def toggle_display_fullscreen(self):
        """Toggle fullscreen"""
        if self.display_window:
            self.display_window.toggle_fullscreen()
            state = "fullscreen" if self.display_window.is_fullscreen else "windowed"
            self.status_label.setText(f"Display switched to {state} mode")
        else:
            QMessageBox.warning(self, "Cảnh báo", "Không có display nào đang mở")
            
    def show_background(self, bg_id):
        """Hiển thị background"""
        if not self.display_window:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng mở display trước")
            return
            
        self.current_mode = bg_id
        
        if bg_id == "00":
            self.display_window.show_background(bg_id)
        elif bg_id == "01":
            self.apply_ranking()
        elif bg_id == "02":
            self.apply_final_results()
            
    def apply_ranking(self, show_popup=True):
        """Apply ranking data"""
        if not self.display_window:
            if show_popup:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng mở display trước")
            return
            
        # Thu thập data
        overlay_data = {'round': self.round_edit.text()}
        
        for rank in self.rank_edits:
            overlay_data[rank] = self.rank_edits[rank].text()
            
        # Thu thập positions
        positions = {}
        try:
            round_pos = self.round_pos_edit.text().split(',')
            positions['round'] = (int(round_pos[0]), int(round_pos[1]))
        except:
            positions['round'] = (1286, 917)
            
        for rank in self.rank_pos_edits:
            try:
                pos = self.rank_pos_edits[rank].text().split(',')
                positions[rank] = (int(pos[0]), int(pos[1]))
            except:
                positions[rank] = None
                
        overlay_data['positions'] = positions
        
        # Font settings
        font_settings = {
            'font_name': self.font_combo.currentText(),
            'rank_font_size': int(self.rank_font_size_edit.text()) if self.rank_font_size_edit.text().isdigit() else 60,
            'round_font_size': int(self.round_font_size_edit.text()) if self.round_font_size_edit.text().isdigit() else 60,
            'color': self.font_color_combo.currentText()
        }
        overlay_data['font_settings'] = font_settings
        
        success = self.display_window.show_background("01", overlay_data)
        
        if success:
            self.current_mode = "01"
            if show_popup:
                QMessageBox.information(self, "Thành công", "Đã cập nhật ranking")
        else:
            if show_popup:
                QMessageBox.critical(self, "Lỗi", "Không thể cập nhật ranking")
                
    def apply_final_results(self, show_popup=True):
        """Apply final results"""
        if not self.display_window:
            if show_popup:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng mở display trước")
            return
            
        # Thu thập data
        overlay_data = {}
        for key in self.final_edits:
            overlay_data[key] = self.final_edits[key].text()
            
        # Thu thập positions
        positions = {}
        for key in self.final_pos_edits:
            try:
                pos = self.final_pos_edits[key].text().split(',')
                positions[key] = (int(pos[0]), int(pos[1]))
            except:
                positions[key] = None
                
        overlay_data['positions'] = positions
        
        # Font settings
        font_settings = {
            'font_name': self.font_combo.currentText(),
            'font_size': int(self.final_font_size_edit.text()) if self.final_font_size_edit.text().isdigit() else 60,
            'color': self.font_color_combo.currentText()
        }
        overlay_data['font_settings'] = font_settings
        
        success = self.display_window.show_background("02", overlay_data)
        
        if success:
            self.current_mode = "02"
            if show_popup:
                QMessageBox.information(self, "Thành công", "Đã cập nhật final results")
        else:
            if show_popup:
                QMessageBox.critical(self, "Lỗi", "Không thể cập nhật final results")
                
    def load_config(self):
        """Load configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Load settings
                self.background_folder = config.get('background_folder', '')
                self.selected_monitor = config.get('selected_monitor', 0)
                
                # Load positions
                self.round_position = config.get('round_position', "1286,917")
                self.round_font_size = config.get('round_font_size', "60")
                
                rank_positions = config.get('rank_positions', {})
                for rank, pos in rank_positions.items():
                    if rank in self.rank_positions:
                        self.rank_positions[rank] = pos
                        
                final_positions = config.get('final_positions', {})
                for key, pos in final_positions.items():
                    if key in self.final_positions:
                        self.final_positions[key] = pos
                        
                # Load font settings
                self.font_name = config.get('font_name', 'arial.ttf')
                self.font_color = config.get('font_color', 'white')
                self.rank_font_size = config.get('rank_font_size', '60')
                self.final_font_size = config.get('final_font_size', '60')
                
            except Exception as e:
                print(f"Lỗi khi load config: {e}")
                
    def save_config(self):
        """Save configuration"""
        try:
            config = {
                'background_folder': self.background_folder,
                'selected_monitor': self.monitor_combo.currentIndex() if hasattr(self, 'monitor_combo') else 0,
                'round_position': self.round_pos_edit.text() if hasattr(self, 'round_pos_edit') else self.round_position,
                'round_font_size': self.round_font_size_edit.text() if hasattr(self, 'round_font_size_edit') else self.round_font_size,
                'rank_positions': {rank: edit.text() for rank, edit in self.rank_pos_edits.items()} if hasattr(self, 'rank_pos_edits') else self.rank_positions,
                'final_positions': {key: edit.text() for key, edit in self.final_pos_edits.items()} if hasattr(self, 'final_pos_edits') else self.final_positions,
                'font_name': self.font_combo.currentText() if hasattr(self, 'font_combo') else self.font_name,
                'font_color': self.font_color_combo.currentText() if hasattr(self, 'font_color_combo') else self.font_color,
                'rank_font_size': self.rank_font_size_edit.text() if hasattr(self, 'rank_font_size_edit') else self.rank_font_size,
                'final_font_size': self.final_font_size_edit.text() if hasattr(self, 'final_font_size_edit') else self.final_font_size
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Lỗi khi save config: {e}")
            
    def closeEvent(self, event):
        """Xử lý sự kiện đóng ứng dụng"""
        self.save_config()
        if self.display_window:
            self.display_window.close()
        event.accept()

def main():
    """Hàm main"""
    app = QApplication(sys.argv)
    app.setApplicationName("ScoShow PyQt")
    app.setOrganizationName("Tournament Display")
    
    try:
        window = TournamentControlPanel()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Lỗi", f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    main()
