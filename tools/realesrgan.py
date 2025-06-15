import subprocess
import os
from PIL import Image

from app import wallpaperCfg

class RealesrganTool:
    def __init__(self):
        self.realesrgan_path = wallpaperCfg.realesrganPath.value
        
    def upscale(self, input_path, output_path, scale_factor):
        """使用realesrgan进行超分辨率处理"""
        if not os.path.exists(self.realesrgan_path):
            return False
            
        cmd = [
            self.realesrgan_path,
            "-i", input_path,
            "-o", output_path,
            # "--outscale", str(scale_factor),
            "-n", "realesrgan-x4plus-anime"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            print(f"超分辨率处理失败: {e}")
            return False
            
    def fit_to_screen(self, image_path, output_path, screen_width, screen_height):
        """超分辨率处理以适配屏幕"""
        img = Image.open(image_path)
        iw, ih = img.size
        
        width_ratio = screen_width / iw
        height_ratio = screen_height / ih
        
        if width_ratio <= 1 and height_ratio <= 1:
            # 不需要放大
            img.save(output_path)
            return output_path
            
        # 需要放大
        scale = int(max(width_ratio, height_ratio))
        scale = max(2, min(scale, 8))  # 限制在2-8之间
        scale = 4
        if self.upscale(image_path, output_path, scale):
            return output_path
        else:
            # 超分失败，采用普通缩放
            img.save(output_path)
            return output_path