from PIL import Image
import subprocess
import hashlib
import os
from app import config

from app.models.settings import wallpaperCfg

class ImageUtils:

    realesrgan_path = wallpaperCfg.realesrganPath.value
        
    def fit_image_to_screen(image_path, cache_path, screen_width, screen_height):
        """将图片缩放到适合屏幕大小"""
        img = Image.open(image_path)
        iw, ih = img.size
        width_ratio = screen_width / iw
        height_ratio = screen_height / ih

        # 判断是否需要缩小
        if iw > 2 * screen_width or ih > 2 * screen_height:
            scale = min(screen_width / iw, screen_height / ih)
            new_size = (int(iw * scale), int(ih * scale))
            img = img.resize(new_size, Image.LANCZOS)
            img.save(cache_path)
            return cache_path
        
        elif wallpaperCfg.realesrganEnabled.value and (width_ratio > 1 or height_ratio > 1):
            print("启用超分：", wallpaperCfg.realesrganEnabled.value)
            # 需要放大
            scale = int(max(width_ratio, height_ratio))
            scale = max(2, min(scale, 8))  # 限制在2-8之间
            scale = 4
            if ImageUtils.upscale(image_path, cache_path, scale):
                print(f"超分辨率处理成功: {image_path} -> {cache_path}")
                return cache_path
            else:
                # 超分失败，采用普通缩放
                img.save(cache_path)
                print(f"超分辨率处理失败，使用普通缩放: {image_path}")
                return cache_path
        
        else:
            # 不需要处理，直接保存副本
            img.save(cache_path)
            print(f"图片已适合屏幕大小，无需处理: {image_path}")
            return cache_path
    
    def upscale(input_path, output_path, scale_factor):
        """使用realesrgan进行超分辨率处理"""
        if not os.path.exists(ImageUtils.realesrgan_path):
            return False

        cmd = [
            ImageUtils.realesrgan_path,
            "-i", input_path,
            "-o", output_path,
            # "--outscale", str(scale_factor),
            "-n", "realesrgan-x4plus-anime"
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if not config.DEBUG_MODE else 0
            )
            return True
        except Exception as e:
            print(f"超分辨率处理失败: {e}")
            return False
    
    def calculate_file_hash(filepath):
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None