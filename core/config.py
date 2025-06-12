import os

class Config:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.WALLPAPER_DIR = r'C:\Users\kaika\OneDrive\图片\#插画'  # 可替换为配置文件读取
        self.INDEX_FILE = os.path.join(self.BASE_DIR, 'wallpaper_index.json')
        self.CACHE_DIR = os.path.join(self.BASE_DIR, 'wallpaper_cache')
        self.EXCLUDE_FILE = os.path.join(self.BASE_DIR, 'excluded.txt')
        self.REALESRGAN_PATH = os.path.join(self.BASE_DIR, "tools", "realesrgan", "realesrgan-ncnn-vulkan.exe")
        self.UI = 'qt'
        
        # 确保目录存在
        os.makedirs(self.CACHE_DIR, exist_ok=True)