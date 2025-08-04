"""
Demo script để test ScoShow
Tạo một vài ảnh mẫu để test slideshow
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_images():
    """Tạo một vài ảnh mẫu để test"""
    
    # Tạo thư mục samples nếu chưa có
    samples_dir = "samples"
    if not os.path.exists(samples_dir):
        os.makedirs(samples_dir)
    
    # Màu sắc cho các ảnh mẫu
    colors = [
        ("#FF6B6B", "Slide 1\nRed Theme"),
        ("#4ECDC4", "Slide 2\nTeal Theme"), 
        ("#45B7D1", "Slide 3\nBlue Theme"),
        ("#FFA726", "Slide 4\nOrange Theme"),
        ("#66BB6A", "Slide 5\nGreen Theme")
    ]
    
    # Tạo từng ảnh
    for i, (color, text) in enumerate(colors, 1):
        # Tạo ảnh 1920x1080
        img = Image.new('RGB', (1920, 1080), color)
        draw = ImageDraw.Draw(img)
        
        # Thêm text vào giữa ảnh
        try:
            # Thử sử dụng font mặc định
            font = ImageFont.load_default()
        except:
            font = None
            
        # Tính toán vị trí text ở giữa
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 6  # Ước tính
            text_height = 11
            
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2
        
        # Vẽ text
        draw.text((x, y), text, fill='white', font=font)
        
        # Thêm viền
        draw.rectangle([50, 50, 1870, 1030], outline='white', width=5)
        
        # Lưu ảnh
        filename = f"{samples_dir}/sample_{i:02d}.png"
        img.save(filename)
        print(f"Đã tạo: {filename}")
    
    print(f"\nĐã tạo {len(colors)} ảnh mẫu trong thư mục '{samples_dir}'")
    print("Bạn có thể sử dụng những ảnh này để test ScoShow")

if __name__ == "__main__":
    create_sample_images()
