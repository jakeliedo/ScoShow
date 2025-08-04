"""
ScoShow - Tournament Ranking Display
Ứng dụng hiển thị bảng xếp hạng tournament trên màn hình mở rộng với điều khiển từ màn hình chính
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import time
from screeninfo import get_monitors

class TournamentDisplayWindow:
    """Cửa sổ hiển thị tournament trên màn hình mở rộng"""
    
    def __init__(self, monitor_index=1):
        self.root = tk.Toplevel()
                   ttk.Button(display_buttons, text="🚀 Open Display", 
                  style='Success.TButton',
                  command=self.open_display).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(display_buttons, text="🔴 Close Display", 
                  style='Warning.TButton',
                  command=self.close_display).pack(side=tk.LEFT)tton(display_buttons, text="🚀 Open Display", 
                  style='Success.TButton',
                  command=self.open_display).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(display_buttons, text="🔴 Close Display", 
                  style='Warning.TButton',
                  command=self.close_display).pack(side=tk.LEFT)ot.title("ScoShow - Tournament Display")
        self.root.configure(bg='black')
        
        # Thiết lập fullscreen trên màn hình mở rộng
        self.setup_monitor(monitor_index)
        
        # Label để hiển thị ảnh
        self.image_label = tk.Label(self.root, bg='black')
        self.image_label.pack(expand=True)
        
        # Ảnh nền hiện tại
        self.current_background = None
        self.background_paths = {}  # {00: path, 01: path, 02: path}
        
        # Font cho text overlay
        self.font_size = 60
        self.font_color = "white"
        
    def setup_monitor(self, monitor_index):
        """Thiết lập cửa sổ trên màn hình được chỉ định"""
        monitors = get_monitors()
        
        if monitor_index < len(monitors):
            monitor = monitors[monitor_index]
            self.root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        else:
            # Nếu không có màn hình mở rộng, sử dụng màn hình chính
            self.root.geometry("470x700+100+100")
            
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        
    def load_background_folder(self, folder_path):
        """Tải thư mục chứa ảnh nền"""
        required_files = ["00.jpg", "01.png", "02.png"]
        found_files = {}
        
        for filename in required_files:
            full_path = os.path.join(folder_path, filename)
            if os.path.exists(full_path):
                # Lấy ID từ tên file (00, 01, 02)
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
            
            # Lấy kích thước cửa sổ
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            if window_width <= 1 or window_height <= 1:
                window_width = 1920
                window_height = 1080
            
            # Resize ảnh để fit màn hình
            image.thumbnail((window_width, window_height), Image.Resampling.LANCZOS)
            
            # Chuyển đổi cho Tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Hiển thị ảnh
            self.image_label.configure(image=photo)
            self.image_label.image = photo  # Giữ tham chiếu
            
            self.current_background = bg_id
            return True
            
        except Exception as e:
            print(f"Lỗi khi hiển thị ảnh nền {bg_id}: {e}")
            return False
            
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
                
    def close(self):
        """Đóng cửa sổ hiển thị"""
        self.root.destroy()

class TournamentControlPanel:
    """Panel điều khiển tournament trên màn hình chính"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ScoShow - Tournament Control")
        
        # Tính toán kích thước cửa sổ dựa trên độ phân giải màn hình
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Sử dụng kích thước cửa sổ rộng hơn để chứa 2 cột song song
        window_width = 820
        window_height = 880

        # Tính toán vị trí để cửa sổ ở giữa màn hình
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Cho phép resize cửa sổ
        self.root.resizable(True, True)
        
        # Đặt kích thước tối thiểu
        self.root.minsize(705, 886)
        
        # Tournament display window
        self.display_window = None
        
        # Background folder path
        self.background_folder = ""
        
        # Current background mode
        self.current_mode = None
        
        # Selected monitor index
        self.selected_monitor = tk.IntVar(value=0)  # Default to first monitor (index 0)
        
        # Config file path
        self.config_file = "scoshow_config.json"
        
        # Text input variables
        self.setup_variables()
        
        # Load config if exists
        self.load_config()
        
        self.setup_ui()
        
    def setup_variables(self):
        """Thiết lập biến cho các ô nhập text và tọa độ"""
        # Variables cho background 01 (ranking update)
        self.round_var = tk.StringVar()
        self.rank_vars = {
            '1st': tk.StringVar(),
            '2nd': tk.StringVar(), 
            '3rd': tk.StringVar(),
            '4th': tk.StringVar(),
            '5th': tk.StringVar(),
            '6th': tk.StringVar(),
            '7th': tk.StringVar(),
            '8th': tk.StringVar(),
            '9th': tk.StringVar(),
            '10th': tk.StringVar()
        }
        
        # Tọa độ điểm gốc cho round
        self.round_position = tk.StringVar(value="1286,917")
        self.round_font_size = tk.StringVar(value="60")
        
        # Tọa độ điểm gốc cho các vị trí rank
        self.rank_positions = {
            '1st': tk.StringVar(value="1000,400"),
            '2nd': tk.StringVar(value="1000,500"),
            '3rd': tk.StringVar(value="1000,600"),
            '4th': tk.StringVar(value="1000,700"),
            '5th': tk.StringVar(value="1000,800"),
            '6th': tk.StringVar(value="1000,900"),
            '7th': tk.StringVar(value="1000,1000"),
            '8th': tk.StringVar(value="2000,400"),
            '9th': tk.StringVar(value="2000,500"),
            '10th': tk.StringVar(value="2000,600")
        }
        
        # Font settings cho ranking
        self.rank_font_size = tk.StringVar(value="60")
        self.font_name = tk.StringVar(value="arial.ttf")
        self.font_color = tk.StringVar(value="white")
        
        # Font options
        self.font_options = [
            "arial.ttf", "times.ttf", "calibri.ttf", "verdana.ttf", 
            "tahoma.ttf", "georgia.ttf", "trebuc.ttf", "comic.ttf"
        ]
        
        # Color options
        self.color_options = [
            "white", "black", "red", "blue", "green", "yellow", 
            "orange", "purple", "pink", "cyan", "magenta", "gray"
        ]
        
        # Variables cho background 02 (final results)
        self.final_vars = {
            'winner': tk.StringVar(),
            'second': tk.StringVar(),
            'third': tk.StringVar(),
            'fourth': tk.StringVar(),
            'fifth': tk.StringVar()
        }
        
        # Tọa độ và font cho final results
        self.final_positions = {
            'winner': tk.StringVar(value="1920,300"),
            'second': tk.StringVar(value="1920,450"),
            'third': tk.StringVar(value="1920,600"),
            'fourth': tk.StringVar(value="1920,750"),
            'fifth': tk.StringVar(value="1920,900")
        }
        self.final_font_size = tk.StringVar(value="60")
        
    def load_config(self):
        """Load configuration từ file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Load positions
                if 'round_position' in config:
                    self.round_position.set(config['round_position'])
                if 'round_font_size' in config:
                    self.round_font_size.set(config['round_font_size'])
                    
                if 'rank_positions' in config:
                    for rank, pos in config['rank_positions'].items():
                        if rank in self.rank_positions:
                            self.rank_positions[rank].set(pos)
                            
                if 'final_positions' in config:
                    for key, pos in config['final_positions'].items():
                        if key in self.final_positions:
                            self.final_positions[key].set(pos)
                            
                # Load font settings
                if 'font_name' in config:
                    self.font_name.set(config['font_name'])
                if 'font_color' in config:
                    self.font_color.set(config['font_color'])
                if 'rank_font_size' in config:
                    self.rank_font_size.set(config['rank_font_size'])
                if 'final_font_size' in config:
                    self.final_font_size.set(config['final_font_size'])
                    
                # Load background folder
                if 'background_folder' in config:
                    self.background_folder = config['background_folder']
                    
                # Load selected monitor
                if 'selected_monitor' in config:
                    monitor_value = config['selected_monitor']
                    # Validate monitor index against available monitors
                    monitors = get_monitors()
                    if monitor_value < len(monitors):
                        self.selected_monitor.set(monitor_value)
                    else:
                        self.selected_monitor.set(0)  # Default to first monitor
                    
        except Exception as e:
            print(f"Lỗi khi load config: {e}")
            
    def save_config(self):
        """Save configuration vào file"""
        try:
            config = {
                'round_position': self.round_position.get(),
                'round_font_size': self.round_font_size.get(),
                'rank_positions': {rank: var.get() for rank, var in self.rank_positions.items()},
                'final_positions': {key: var.get() for key, var in self.final_positions.items()},
                'font_name': self.font_name.get(),
                'font_color': self.font_color.get(),
                'rank_font_size': self.rank_font_size.get(),
                'final_font_size': self.final_font_size.get(),
                'background_folder': self.background_folder,
                'selected_monitor': self.selected_monitor.get()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Lỗi khi save config: {e}")
        
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')  # Modern theme
        
        # Configure styles with colors
        style.configure('Title.TLabel', 
                       foreground='#2C3E50',
                       font=('Arial', 18, 'bold'))
        
        # Configure LabelFrame style properly
        style.configure('Header.TLabelFrame.Label', 
                       foreground='#34495E',
                       font=('Arial', 10, 'bold'))
        
        style.configure('Action.TButton',
                       foreground='white',
                       font=('Arial', 9, 'bold'))
        
        style.map('Action.TButton',
                 background=[('active', '#3498DB'),
                           ('!active', '#2980B9')])
        
        style.configure('Success.TButton',
                       foreground='white',
                       font=('Arial', 9, 'bold'))
        
        style.map('Success.TButton',
                 background=[('active', '#27AE60'),
                           ('!active', '#229954')])
        
        style.configure('Warning.TButton',
                       foreground='white',
                       font=('Arial', 9, 'bold'))
        
        style.map('Warning.TButton',
                 background=[('active', '#F39C12'),
                           ('!active', '#E67E22')])
        
        # Main container with background color
        self.root.configure(bg='#ECF0F1')
        
        # Tạo Canvas và Scrollbar cho khả năng cuộn
        main_canvas = tk.Canvas(self.root, bg='#ECF0F1', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        # Cấu hình scrollable frame
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas và scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel để cuộn
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Frame chính với padding trong scrollable frame
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header với tiêu đề và logo - compact hơn
        header_frame = tk.Frame(main_frame, bg='#2C3E50', height=60)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        header_frame.pack_propagate(False)
        
        # Tiêu đề chính
        title_frame = tk.Frame(header_frame, bg='#2C3E50')
        title_frame.pack(expand=True)
        
        title_label = tk.Label(title_frame, 
                              text="🏆 ScoShow - Tournament Ranking", 
                              font=('Arial', 16, 'bold'),
                              bg='#2C3E50',
                              fg='#ECF0F1')
        title_label.pack(pady=8)
        
        subtitle_label = tk.Label(title_frame,
                                 text="Professional Tournament Display System",
                                 font=('Arial', 9, 'italic'),
                                 bg='#2C3E50',
                                 fg='#BDC3C7')
        subtitle_label.pack()
        
        # Tạo container chính để chứa 2 cột song song
        content_container = ttk.Frame(main_frame)
        content_container.pack(fill=tk.BOTH, expand=True)
        
        # Cột trái cho các thành phần chính
        left_column = ttk.Frame(content_container)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Cột phải cho Final Results
        right_column = ttk.Frame(content_container)
        right_column.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Frame cho việc chọn màn hình (cột trái)
        monitor_frame = ttk.LabelFrame(left_column, text="🖥️  Monitor Setup", 
                                      padding="10")
        monitor_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Hiển thị thông tin màn hình với icon
        monitors = get_monitors()
        monitor_info = f"📺 Detected {len(monitors)} monitor(s)"
        info_label = ttk.Label(monitor_frame, text=monitor_info, 
                              font=('Arial', 9, 'bold'),
                              foreground='#2980B9')
        info_label.pack()
        
        # Thêm tùy chọn chọn màn hình
        monitor_selection_frame = ttk.Frame(monitor_frame)
        monitor_selection_frame.pack(pady=(5, 0))
        
        ttk.Label(monitor_selection_frame, text="Display on Monitor:").pack(side=tk.LEFT, padx=(0, 5))
        
        for i, monitor in enumerate(monitors):
            monitor_radio = ttk.Radiobutton(
                monitor_selection_frame,
                text=f"Monitor {i+1} ({monitor.width}x{monitor.height})",
                variable=self.selected_monitor,
                value=i
            )
            monitor_radio.pack(side=tk.LEFT, padx=(0, 10))
        
        if len(monitors) > 1:
            status_text = "✅ Multiple monitors available - Choose monitor above"
            color = '#27AE60'
        else:
            status_text = "⚠️  Only 1 monitor - will display in window"
            color = '#F39C12'
            
        status_label = ttk.Label(monitor_frame, text=status_text,
                                foreground=color, font=('Arial', 8))
        status_label.pack(pady=(3, 0))
        
        # Frame cho việc chọn thư mục background (cột trái)
        bg_frame = ttk.LabelFrame(left_column, text="🖼️  Background Setup", 
                                 padding="10")
        bg_frame.pack(fill=tk.X, pady=(0, 10))
        
        bg_button_frame = ttk.Frame(bg_frame)
        bg_button_frame.pack(fill=tk.X)
        
        ttk.Button(bg_button_frame, text="📁 Select Background Folder", 
                  style='Action.TButton',
                  command=self.select_background_folder).pack(side=tk.LEFT, padx=(0, 15))
        
        self.bg_status_label = ttk.Label(bg_button_frame, text="❌ No folder selected",
                                        foreground='#E74C3C',
                                        font=('Arial', 9, 'bold'))
        self.bg_status_label.pack(side=tk.LEFT)
        
        # Frame điều khiển hiển thị (cột trái)
        display_frame = ttk.LabelFrame(left_column, text="🎮  Display Control", 
                                      padding="10")
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Nút mở/đóng display
        display_buttons = ttk.Frame(display_frame)
        display_buttons.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Button(display_buttons, text="🚀 Open Display", 
                  style='Success.TButton',
                  command=self.open_display).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(display_buttons, text="� Switch Monitor", 
                  style='Action.TButton',
                  command=self.switch_monitor).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(display_buttons, text="�🔴 Close Display", 
                  style='Warning.TButton',
                  command=self.close_display).pack(side=tk.LEFT)
                  
        # Nút chọn background
        bg_buttons = ttk.Frame(display_frame)
        bg_buttons.pack(fill=tk.X)
        
        ttk.Button(bg_buttons, text="⏸️  Show 00 (Waiting)", 
                  style='Action.TButton',
                  command=lambda: self.show_background("00")).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bg_buttons, text="📊 Show 01 (Ranking)", 
                  style='Success.TButton',
                  command=lambda: self.show_background("01")).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bg_buttons, text="🏆 Show 02 (Final)", 
                  style='Warning.TButton',
                  command=lambda: self.show_background("02")).pack(side=tk.LEFT)
        
        # Frame cho input ranking (cột trái)
        self.ranking_frame = ttk.LabelFrame(left_column, text="📊 Ranking Input (Background 01)", 
                                           padding="10")
        self.ranking_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Font settings frame với màu sắc - compact hơn
        font_frame = tk.Frame(self.ranking_frame, bg='#F8F9FA')
        font_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(font_frame, text="🎨 Font Settings", 
                font=('Arial', 9, 'bold'),
                bg='#F8F9FA', fg='#2C3E50').pack(pady=(3, 5))
        
        font_controls = ttk.Frame(font_frame)
        font_controls.pack()
        
        ttk.Label(font_controls, text="Font:").pack(side=tk.LEFT)
        font_combo = ttk.Combobox(font_controls, textvariable=self.font_name, 
                                 values=self.font_options, width=12, state="readonly")
        font_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(font_controls, text="Size:").pack(side=tk.LEFT)
        ttk.Entry(font_controls, textvariable=self.rank_font_size, width=4).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(font_controls, text="Color:").pack(side=tk.LEFT)
        color_combo = ttk.Combobox(font_controls, textvariable=self.font_color, 
                                  values=self.color_options, width=8, state="readonly")
        color_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Round input với style đẹp - compact hơn
        round_container = tk.Frame(self.ranking_frame, bg='#E8F4FD')
        round_container.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(round_container, text="🔄 Round Settings", 
                font=('Arial', 9, 'bold'),
                bg='#E8F4FD', fg='#2980B9').pack(pady=(3, 3))
        
        round_frame = ttk.Frame(round_container)
        round_frame.pack(pady=(0, 5))
        
        ttk.Label(round_frame, text="Round:").pack(side=tk.LEFT)
        ttk.Entry(round_frame, textvariable=self.round_var, width=8).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(round_frame, text="Position (x,y):").pack(side=tk.LEFT)
        ttk.Entry(round_frame, textvariable=self.round_position, width=12).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(round_frame, text="Font Size:").pack(side=tk.LEFT)
        ttk.Entry(round_frame, textvariable=self.round_font_size, width=4).pack(side=tk.LEFT, padx=(5, 0))
        
        # Ranking inputs - chia thành 2 cột với style đẹp - compact hơn
        ranking_input_frame = ttk.Frame(self.ranking_frame)
        ranking_input_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Cột 1: 1st - 5th với background màu
        col1_container = tk.Frame(ranking_input_frame, bg='#E8F6F3')
        col1_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(col1_container, text="🥇 Ranks 1-5", 
                font=('Arial', 9, 'bold'),
                bg='#E8F6F3', fg='#27AE60').pack(pady=(5, 3))
        
        col1_frame = ttk.Frame(col1_container)
        col1_frame.pack(padx=8, pady=(0, 5))
        
        for rank in ['1st', '2nd', '3rd', '4th', '5th']:
            rank_frame = ttk.Frame(col1_frame)
            rank_frame.pack(fill=tk.X, pady=(0, 2))
            ttk.Label(rank_frame, text=f"{rank}:", width=5).pack(side=tk.LEFT)
            ttk.Entry(rank_frame, textvariable=self.rank_vars[rank], width=14).pack(side=tk.LEFT, padx=(3, 3))
            ttk.Entry(rank_frame, textvariable=self.rank_positions[rank], width=8).pack(side=tk.LEFT, padx=(3, 0))
            
        # Cột 2: 6th - 10th với background màu
        col2_container = tk.Frame(ranking_input_frame, bg='#FDF2E9')
        col2_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(col2_container, text="🥉 Ranks 6-10", 
                font=('Arial', 9, 'bold'),
                bg='#FDF2E9', fg='#E67E22').pack(pady=(5, 3))
        
        col2_frame = ttk.Frame(col2_container)
        col2_frame.pack(padx=8, pady=(0, 5))
        
        for rank in ['6th', '7th', '8th', '9th', '10th']:
            rank_frame = ttk.Frame(col2_frame)
            rank_frame.pack(fill=tk.X, pady=(0, 2))
            ttk.Label(rank_frame, text=f"{rank}:", width=5).pack(side=tk.LEFT)
            ttk.Entry(rank_frame, textvariable=self.rank_vars[rank], width=14).pack(side=tk.LEFT, padx=(3, 3))
            ttk.Entry(rank_frame, textvariable=self.rank_positions[rank], width=8).pack(side=tk.LEFT, padx=(3, 0))
            
        # Apply button cho ranking với style đẹp
        ttk.Button(self.ranking_frame, text="✅ Apply Ranking", 
                  style='Success.TButton',
                  command=self.apply_ranking).pack(pady=(8, 0))
        
        # Frame cho input final results (cột phải) - compact và song song với ranking
        self.final_frame = ttk.LabelFrame(right_column, text="🏆 Final Results Input (Background 02)", 
                                         padding="10")
        self.final_frame.pack(fill=tk.BOTH, expand=True)
        
        # Font settings cho final results với background - đầy đủ tùy chọn
        final_font_container = tk.Frame(self.final_frame, bg='#FEF9E7')
        final_font_container.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(final_font_container, text="🎨 Final Results Font", 
                font=('Arial', 9, 'bold'),
                bg='#FEF9E7', fg='#F39C12').pack(pady=(3, 3))
        
        final_font_frame = ttk.Frame(final_font_container)
        final_font_frame.pack(pady=(0, 5))
        
        # Font selection cho final results
        ttk.Label(final_font_frame, text="Font:").pack(side=tk.LEFT)
        final_font_combo = ttk.Combobox(final_font_frame, textvariable=self.font_name, 
                                       values=self.font_options, width=10, state="readonly")
        final_font_combo.pack(side=tk.LEFT, padx=(5, 8))
        
        ttk.Label(final_font_frame, text="Size:").pack(side=tk.LEFT)
        ttk.Entry(final_font_frame, textvariable=self.final_font_size, width=4).pack(side=tk.LEFT, padx=(5, 8))
        
        ttk.Label(final_font_frame, text="Color:").pack(side=tk.LEFT)
        final_color_combo = ttk.Combobox(final_font_frame, textvariable=self.font_color, 
                                        values=self.color_options, width=6, state="readonly")
        final_color_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # Final result inputs với style đẹp - compact hơn
        results_container = tk.Frame(self.final_frame, bg='#FDEDEC')
        results_container.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(results_container, text="🏅 Championship Rankings", 
                font=('Arial', 9, 'bold'),
                bg='#FDEDEC', fg='#E74C3C').pack(pady=(3, 5))
        
        results_frame = ttk.Frame(results_container)
        results_frame.pack(padx=8, pady=(0, 5))
        
        final_labels = {'winner': '🥇 1st Place:', 'second': '🥈 2nd Place:', 'third': '🥉 3rd Place:', 
                       'fourth': '🏅 4th Place:', 'fifth': '🎖️ 5th Place:'}
        for key, label in final_labels.items():
            final_rank_frame = ttk.Frame(results_frame)
            final_rank_frame.pack(fill=tk.X, pady=(0, 3))
            ttk.Label(final_rank_frame, text=label, width=12).pack(side=tk.LEFT)
            ttk.Entry(final_rank_frame, textvariable=self.final_vars[key], width=15).pack(side=tk.LEFT, padx=(3, 3))
            
            # Tọa độ điểm gốc - đặt ở dòng tiếp theo để tiết kiệm chỗ
            pos_frame = ttk.Frame(results_frame)
            pos_frame.pack(fill=tk.X, pady=(0, 5))
            ttk.Label(pos_frame, text="Position:", width=8).pack(side=tk.LEFT)
            ttk.Entry(pos_frame, textvariable=self.final_positions[key], width=15).pack(side=tk.LEFT, padx=(3, 0))
            
        # Apply button cho final results với style đẹp
        ttk.Button(self.final_frame, text="🏆 Apply Final Results", 
                  style='Warning.TButton',
                  command=self.apply_final_results).pack(pady=(8, 0))
        
        # Status label với style đẹp - compact hơn (cột trái)
        status_container = tk.Frame(left_column, bg='#E8F6F3')
        status_container.pack(fill=tk.X, pady=(10, 5))
        
        tk.Label(status_container, text="📊 System Status", 
                font=('Arial', 9, 'bold'),
                bg='#E8F6F3', fg='#27AE60').pack(pady=(5, 3))
        
        self.status_label = tk.Label(status_container, text="Ready to start tournament display", 
                                   font=('Arial', 8),
                                   bg='#E8F6F3', fg='#2C3E50',
                                   relief=tk.FLAT,
                                   padx=8, pady=5)
        self.status_label.pack(pady=(0, 5))
        
    def select_background_folder(self):
        """Chọn thư mục chứa ảnh background"""
        folder = filedialog.askdirectory(title="Chọn thư mục chứa background (00.jpg, 01.png, 02.png)")
        if folder:
            self.background_folder = folder
            # Kiểm tra xem có đủ 3 file background không
            required_files = ["00.jpg", "01.png", "02.png"]
            missing_files = []
            
            for filename in required_files:
                if not os.path.exists(os.path.join(folder, filename)):
                    missing_files.append(filename)
                    
            if missing_files:
                messagebox.showwarning("Cảnh báo", 
                    f"Thiếu các file: {', '.join(missing_files)}")
                self.bg_status_label.config(text="Thiếu file background")
            else:
                self.bg_status_label.config(text="✓ Background OK")
                
    def open_display(self):
        """Mở hoặc chuyển đổi cửa sổ hiển thị tournament"""
        if not self.background_folder:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục background trước")
            return
            
        monitors = get_monitors()
        monitor_index = self.selected_monitor.get()
        
        # Ensure monitor_index is valid
        if monitor_index >= len(monitors):
            monitor_index = 0
            self.selected_monitor.set(0)
            
        print(f"Attempting to open/switch display to monitor {monitor_index + 1}")
        
        # Close existing display window if it's open
        if self.display_window:
            self.display_window.close()
            self.display_window = None
            
        # Create a new display window on the selected monitor
        self.display_window = TournamentDisplayWindow(monitor_index)
        
        # Load background folder and restore state
        if self.display_window.load_background_folder(self.background_folder):
            self.status_label.config(text=f"Display opened on Monitor {monitor_index + 1}")
            
            # Restore the last shown background
            if self.current_mode:
                if self.current_mode == "00":
                    self.display_window.show_background("00")
                elif self.current_mode == "01":
                    self.apply_ranking(show_popup=False) # Avoid popup on switch
                elif self.current_mode == "02":
                    self.apply_final_results(show_popup=False) # Avoid popup on switch
        else:
            messagebox.showerror("Lỗi", "Không thể load background")
            self.display_window.close()
            self.display_window = None
            
    def close_display(self):
        """Đóng cửa sổ hiển thị tournament"""
        if self.display_window:
            self.display_window.close()
            self.display_window = None
            # Don't clear current_mode, so it can be restored
            self.status_label.config(text="Display closed")
            print("Display window closed")
        else:
            messagebox.showinfo("Thông báo", "Không có display nào đang mở")
    
    def show_background(self, bg_id):
        """Hiển thị background được chọn"""
        if not self.display_window:
            messagebox.showwarning("Cảnh báo", "Vui lòng mở display trước")
            return
            
        self.current_mode = bg_id
        
        if bg_id == "00":
            # Background chờ - chỉ hiển thị ảnh
            success = self.display_window.show_background(bg_id)
        elif bg_id == "01":
            # Background ranking - hiển thị với data hiện tại
            self.apply_ranking()
            return
        elif bg_id == "02":
            # Background final - hiển thị với data hiện tại  
            self.apply_final_results()
            return
            
        # Không hiển thị popup cho việc chuyển background
            
    def apply_ranking(self, show_popup=True):
        """Apply ranking data lên background 01"""
        if not self.display_window:
            messagebox.showwarning("Cảnh báo", "Vui lòng mở display trước")
            return
            
        # Thu thập data từ input fields
        overlay_data = {
            'round': self.round_var.get()
        }
        
        for rank, var in self.rank_vars.items():
            overlay_data[rank] = var.get()
            
        # Thu thập tọa độ điểm gốc
        positions = {}
        try:
            round_pos = self.round_position.get().split(',')
            positions['round'] = (int(round_pos[0]), int(round_pos[1]))
        except (ValueError, IndexError):
            positions['round'] = (1286, 917)  # default
            
        for rank, pos_var in self.rank_positions.items():
            try:
                pos = pos_var.get().split(',')
                positions[rank] = (int(pos[0]), int(pos[1]))
            except (ValueError, IndexError):
                positions[rank] = None
                
        overlay_data['positions'] = positions
        
        # Thu thập font settings
        font_settings = {
            'font_name': self.font_name.get(),
            'rank_font_size': int(self.rank_font_size.get()) if self.rank_font_size.get().isdigit() else 60,
            'round_font_size': int(self.round_font_size.get()) if self.round_font_size.get().isdigit() else 60,
            'color': self.font_color.get()
        }
        overlay_data['font_settings'] = font_settings
        
        # Hiển thị background với overlay
        success = self.display_window.show_background("01", overlay_data)
        
        if success:
            self.current_mode = "01"
            if show_popup:
                messagebox.showinfo("Thành công", "Đã cập nhật ranking")
        else:
            if show_popup:
                messagebox.showerror("Lỗi", "Không thể cập nhật ranking")
            
    def apply_final_results(self, show_popup=True):
        """Apply final results lên background 02"""
        if not self.display_window:
            messagebox.showwarning("Cảnh báo", "Vui lòng mở display trước")
            return
            
        # Thu thập data từ input fields
        overlay_data = {}
        for key, var in self.final_vars.items():
            overlay_data[key] = var.get()
            
        # Thu thập tọa độ điểm gốc cho final results
        positions = {}
        for key, pos_var in self.final_positions.items():
            try:
                pos = pos_var.get().split(',')
                positions[key] = (int(pos[0]), int(pos[1]))
            except (ValueError, IndexError):
                positions[key] = None
                
        overlay_data['positions'] = positions
        
        # Font settings cho final results
        font_settings = {
            'font_name': self.font_name.get(),
            'font_size': int(self.final_font_size.get()) if self.final_font_size.get().isdigit() else 60,
            'color': self.font_color.get()
        }
        overlay_data['font_settings'] = font_settings
        
        # Hiển thị background với overlay
        success = self.display_window.show_background("02", overlay_data)
        
        if success:
            self.current_mode = "02"
            if show_popup:
                messagebox.showinfo("Thành công", "Đã cập nhật final results")
        else:
            if show_popup:
                messagebox.showerror("Lỗi", "Không thể cập nhật final results")
            
    def run(self):
        """Chạy ứng dụng"""
        # Update background folder status nếu có config
        if self.background_folder and os.path.exists(self.background_folder):
            self.bg_status_label.config(text="✓ Background OK")
            
        # Xử lý sự kiện đóng ứng dụng
        def on_closing():
            self.save_config()  # Save config khi đóng
            if self.display_window:
                self.display_window.close()
            self.root.destroy()
            
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

def main():
    """Hàm main"""
    try:
        app = TournamentControlPanel()
        app.run()
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {e}")

if __name__ == "__main__":
    main()
