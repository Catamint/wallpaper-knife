from PIL import Image
import os

class ImageUtils:
    def __init__(self, config):
        self.config = config
        
    def fit_image_to_screen(self, image_path, cache_path, screen_width, screen_height):
        """将图片缩放到适合屏幕大小"""
        img = Image.open(image_path)
        iw, ih = img.size

        # 判断是否需要缩小
        if iw > 2 * screen_width or ih > 2 * screen_height:
            scale = min(screen_width / iw, screen_height / ih)
            new_size = (int(iw * scale), int(ih * scale))
            img = img.resize(new_size, Image.LANCZOS)
            img.save(cache_path)
            return cache_path

        # 检查是否需要放大 - 调用tools模块处理
        # 这里保持方法签名不变, 实际逻辑移至RealesrganTool类

        # 不需要处理，直接保存副本
        img.save(cache_path)
        return cache_path