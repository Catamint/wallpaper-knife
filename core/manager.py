import os
import json
import random
import ctypes
import threading
import time
import base64
from io import BytesIO
from PIL import Image  # 使用 Pillow 处理图像

class WallpaperManager:
    def __init__(self, config, file_utils):
        self.config = config
        self.file_utils = file_utils
        self.index_data = {
            "wallpapers": {},
            "total_count": 0,
            "last_updated": None
        }
        # 壁纸设置线程
        self.wallpaper_setter_thread = None
        self.wallpaper_setter_event = threading.Event()
        
    def _create_thumbnail_base64(self, image_path, max_size=(120, 120)):
        """创建图片的缩略图并返回base64编码
        
        Args:
            image_path: 图片路径
            max_size: 缩略图最大尺寸 (宽, 高)
            
        Returns:
            str: base64编码的缩略图，失败返回None
        """
        try:
            # 打开图像
            with Image.open(image_path) as img:
                # 调整图像大小，保持宽高比
                img.thumbnail(max_size, Image.LANCZOS)
                
                # 转换为RGB模式 (处理RGBA等格式)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 保存到内存缓冲区
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                # 转换为base64
                img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                return img_base64
                
        except Exception as e:
            print(f"创建缩略图失败: {image_path}, 错误: {e}")
            return None
    
    def build_index(self, progress_callback=None):
        """构建壁纸索引，不立即生成缩略图"""
        if not os.path.exists(self.config.WALLPAPER_DIR):
            return False
            
        # 加载旧索引
        old_index = {}
        if os.path.exists(self.config.INDEX_FILE):
            try:
                with open(self.config.INDEX_FILE, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    old_index = old_data.get("wallpapers", {})
            except Exception as e:
                print(f"加载旧索引失败: {e}")
        
        # 存储文件列表
        image_files = []
        
        # 递归扫描目录获取所有图片文件
        for root, _, files in os.walk(self.config.WALLPAPER_DIR):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                    # 构建绝对路径
                    filepath = os.path.join(root, file)
                    # 存储相对路径与绝对路径
                    rel_path = os.path.relpath(filepath, self.config.WALLPAPER_DIR)
                    image_files.append((rel_path, filepath))
        
        new_wallpapers = {}
        total_files = len(image_files)
        
        for i, (rel_path, filepath) in enumerate(image_files):
            if progress_callback:
                progress_callback(i, total_files, rel_path)
                
            file_hash = self.file_utils.calculate_file_hash(filepath)
            
            if file_hash:
                # 检查是否在旧索引中存在相同hash的文件
                existing_data = None
                old_key = None
                for old_key_name, old_data in old_index.items():
                    if old_data.get("hash") == file_hash:
                        existing_data = old_data.copy()
                        old_key = old_key_name
                        # 更新路径
                        existing_data["path"] = filepath
                        existing_data["relative_path"] = rel_path
                        break
            
            # 构建新的键名，使用哈希值前12位+文件名
            filename = os.path.basename(filepath)
            key = f"{file_hash[:12]}_{filename}"
            
            if existing_data:
                # 继承旧属性
                new_wallpapers[key] = existing_data
                # 验证缓存文件是否存在
                if existing_data.get("cache_path"):
                    cache_full_path_file = os.path.join(self.config.CACHE_DIR, existing_data["cache_path"])
                    if not os.path.exists(cache_full_path_file):
                        existing_data["cache_path"] = None
                        existing_data["crop_region"] = None
            else:
                # 新文件 - 不立即生成缩略图
                new_wallpapers[key] = {
                    "hash": file_hash,
                    "path": filepath,
                    "relative_path": rel_path,
                    "display_name": filename,
                    "crop_region": None,
                    "cache_path": None,
                    "view_pic": None,  # 初始为None，按需加载
                    "excluded": False,
                }
    
        self.index_data["wallpapers"] = new_wallpapers
        self.index_data["total_count"] = len(new_wallpapers)
        self.index_data["last_updated"] = os.path.getmtime(self.config.WALLPAPER_DIR)
        
        self.save_index()
        return True
        
    def load_index(self):
        """加载索引文件"""
        if not os.path.exists(self.config.INDEX_FILE):
            return False
            
        try:
            with open(self.config.INDEX_FILE, 'r', encoding='utf-8') as f:
                self.index_data = json.load(f)
            return True
        except Exception as e:
            print(f"加载索引失败: {e}")
            return False
    
    def save_index(self):
        """保存索引文件"""
        try:
            with open(self.config.INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存索引失败: {e}")
            
    def update_crop_region(self, filename, crop_region, cache_filename=None):
        """更新裁剪区域"""
        if filename in self.index_data["wallpapers"]:
            self.index_data["wallpapers"][filename]["crop_region"] = crop_region
            if cache_filename:
                self.index_data["wallpapers"][filename]["cache_path"] = cache_filename
            self.save_index()
    
    def get_wallpaper_list(self):
        """获取壁纸列表"""
        return list(self.index_data["wallpapers"].keys())
        
    def set_wallpaper(self, image_path, async_mode=True):
        """设置壁纸，可异步"""
        if async_mode:
            # 取消上一次的壁纸设置
            if self.wallpaper_setter_thread and self.wallpaper_setter_thread.is_alive():
                self.wallpaper_setter_event.set()
                self.wallpaper_setter_thread.join(timeout=0.1)
            self.wallpaper_setter_event.clear()
            
            # 启动异步线程延迟设置壁纸
            def setter(path, cancel_event):
                time.sleep(0.5)  # 延迟响应
                if not cancel_event.is_set():
                    try:
                        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
                    except Exception as e:
                        print(f"设置壁纸失败: {e}")

            self.wallpaper_setter_thread = threading.Thread(
                target=setter, args=(image_path, self.wallpaper_setter_event), daemon=True
            )
            self.wallpaper_setter_thread.start()
        else:
            # 同步设置
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
            except Exception as e:
                print(f"设置壁纸失败: {e}")
    
    def get_thumbnail_base64(self, filename):
        """获取壁纸缩略图的base64编码，如果不存在则生成"""
        if filename not in self.index_data["wallpapers"]:
            return None
        
        wallpaper = self.index_data["wallpapers"][filename]
        
        # 如果已有缩略图，直接返回
        if wallpaper.get("view_pic"):
            return wallpaper["view_pic"]
        
        # 否则生成缩略图
        image_path = wallpaper["path"]
        thumbnail = self._create_thumbnail_base64(image_path)
        
        # 更新索引并保存
        wallpaper["view_pic"] = thumbnail
        self.save_index()
        
        return thumbnail
