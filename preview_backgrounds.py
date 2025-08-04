"""
Script để xem trước các ảnh nền và phân tích layout
"""

from PIL import Image, ImageDraw
import os

def preview_backgrounds():
    """Xem thông tin các ảnh nền"""
    background_dir = "background"
    
    if not os.path.exists(background_dir):
        print("Thư mục background không tồn tại!")
        return
    
    files = ["00.jpg", "01.png", "02.png"]
    
    for filename in files:
        filepath = os.path.join(background_dir, filename)
        if os.path.exists(filepath):
            try:
                img = Image.open(filepath)
                print(f"\n--- {filename} ---")
                print(f"Kích thước: {img.size[0]} x {img.size[1]}")
                print(f"Định dạng: {img.format}")
                print(f"Mode: {img.mode}")
                
                # Mô tả mục đích sử dụng
                if filename == "00.jpg":
                    print("Mục đích: Hình nền chờ trong lúc update thứ hạng")
                elif filename == "01.png":
                    print("Mục đích: Hình nền update thứ hạng (có sẵn vị trí rank và round)")
                elif filename == "02.png":
                    print("Mục đích: Hình nền công bố kết quả cuối cùng")
                    
            except Exception as e:
                print(f"Lỗi khi đọc {filename}: {e}")
        else:
            print(f"Không tìm thấy file: {filename}")

def analyze_round_position():
    """Phân tích tọa độ và kích thước ô text dành cho thứ tự round"""
    filepath = "background/01.png"
    if os.path.exists(filepath):
        try:
            img = Image.open(filepath)
            draw = ImageDraw.Draw(img)
            
            # Tọa độ và kích thước ô text (giả định)
            round_box = (1920, 200, 2100, 300)  # (x1, y1, x2, y2)
            
            # Vẽ ô text lên ảnh để kiểm tra
            draw.rectangle(round_box, outline="red", width=3)
            
            # Lưu ảnh để xem trước
            img.save("background/01_preview.png")
            print(f"Tọa độ ô text dành cho thứ tự round: {round_box}")
            print("Đã lưu ảnh preview tại: background/01_preview.png")
        except Exception as e:
            print(f"Lỗi khi phân tích ảnh: {e}")
    else:
        print("Không tìm thấy file: background/01.png")

if __name__ == "__main__":
    preview_backgrounds()
    analyze_round_position()
