import os
import json
import random
import ctypes
import threading
import time
import base64
import datetime
from io import BytesIO
from PIL import Image  # 使用 Pillow 处理图像
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from .picture import Picture
from app.utils.image_utils import ImageUtils  # 确保图像处理工具类已正确导入

from app import wallpaperCfg # 确保配置类已正确导入

class WallpaperIndex:
    """壁纸索引管理类"""
    
    def __init__(self):
        self.wallpapers: Dict[str, Picture] = {}
        self.total_count: int = 0
        self.last_updated: Optional[float] = None
        self._modified: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WallpaperIndex':
        """从字典创建索引"""
        index = cls()
        index.wallpapers = {
            k: Picture.from_dict(v) if isinstance(v, dict) else v 
            for k, v in data.get("wallpapers", {}).items()
        }
        index.total_count = data.get("total_count", len(index.wallpapers))
        index.last_updated = data.get("last_updated")
        return index
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "wallpapers": {k: v.to_dict() for k, v in self.wallpapers.items()},
            "total_count": self.total_count,
            "last_updated": self.last_updated
        }
    
    def add_picture(self, key: str, picture: Picture) -> None:
        """添加图片"""
        self.wallpapers[key] = picture
        self._modified = True
        self.recount()
    
    def remove_picture(self, key: str) -> bool:
        """删除图片"""
        if key in self.wallpapers:
            del self.wallpapers[key]
            self._modified = True
            self.recount()
            return True
        return False
    
    def get_picture(self, key: str) -> Optional[Picture]:
        """获取图片"""
        pic = self.wallpapers.get(key)
        if pic:
            pic.update_access_time()
        return pic
    
    def get_all_keys(self) -> List[str]:
        """获取所有键"""
        return list(self.wallpapers.keys())
    
    def get_filtered_keys(self, excluded: bool = False) -> List[str]:
        """获取过滤后的键列表"""
        return [k for k, v in self.wallpapers.items() if v.excluded == excluded]
    
    def search_by_name(self, query: str) -> List[str]:
        """按名称搜索"""
        query = query.lower()
        return [k for k, v in self.wallpapers.items() 
                if query in v.display_name.lower() or query in v.path.lower()]
    
    def search_by_hash(self, hash_value: str) -> Optional[str]:
        """按哈希值搜索"""
        for k, v in self.wallpapers.items():
            if v.hash == hash_value:
                return k
        return None
    
    def recount(self) -> None:
        """重新计数"""
        self.total_count = len(self.wallpapers)
        self._modified = True
    
    def update_timestamp(self) -> None:
        """更新时间戳"""
        self.last_updated = time.time()
        self._modified = True
    
    def is_modified(self) -> bool:
        """索引是否被修改"""
        if self._modified:
            return True
        
        # 检查任何图片是否被修改
        for pic in self.wallpapers.values():
            if pic.is_modified():
                return True
        
        return False
    
    def mark_saved(self) -> None:
        """标记为已保存"""
        self._modified = False
        for pic in self.wallpapers.values():
            pic.mark_saved()


class WallpaperManager:
    """壁纸管理器"""
    def __init__(self):
        self.config = wallpaperCfg
        self.index = WallpaperIndex()
        self.wallpaper_setter_thread = None
        self.wallpaper_setter_event = threading.Event()
        self.auto_save_timer = None
        self._start_auto_save()
    
    def _start_auto_save(self, interval: int = 300) -> None:
        """启动自动保存定时器"""
        def auto_save():
            while True:
                time.sleep(interval)
                if self.index.is_modified():
                    self.save_index()
        
        self.auto_save_timer = threading.Thread(
            target=auto_save, daemon=True
        )
        self.auto_save_timer.start()
    
    def _create_thumbnail_base64(self, image_path: str, max_size: Tuple[int, int] = (120, 120)) -> Optional[str]:
        """创建图片缩略图并返回base64编码"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_size, Image.LANCZOS)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                buffer.seek(0)
                
                return base64.b64encode(buffer.read()).decode('utf-8')
                
        except Exception as e:
            print(f"创建缩略图失败: {image_path}, 错误: {e}")
            return None
    
    def _generate_key_from_file(self, file_hash: str, filename: str) -> str:
        """从文件信息生成唯一键"""
        return f"{file_hash[:12]}_{filename}"
    
    def build_index(self, progress_callback: Callable = None) -> bool:
        """构建壁纸索引，增量更新"""
        if not os.path.exists(self.config.wallpaperDir.value):
            return False
            
        # 先加载现有索引
        self.load_index()
        
        # 暂存已知文件的哈希值，用于快速查找
        existing_hashes = {pic.hash: key for key, pic in self.index.wallpapers.items()}
        
        # 扫描文件系统
        image_files = []
        for root, _, files in os.walk(self.config.wallpaperDir.value):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, self.config.wallpaperDir.value)
                    image_files.append((rel_path, filepath))
        
        # 跟踪已处理文件，用于检测删除的文件
        processed_keys = set()
        total_files = len(image_files)
        
        for i, (rel_path, filepath) in enumerate(image_files):
            if progress_callback:
                progress_callback(i, total_files, rel_path)
                
            file_hash = ImageUtils.calculate_file_hash(filepath)
            if not file_hash:
                continue
                
            filename = os.path.basename(filepath)
            key = self._generate_key_from_file(file_hash, filename)
            processed_keys.add(key)
            
            # 检查是否存在具有相同哈希的文件
            if file_hash in existing_hashes:
                existing_key = existing_hashes[file_hash]
                pic = self.index.get_picture(existing_key)
                
                # 路径可能有变化
                if pic.path != filepath:
                    pic.update_path(filepath, rel_path)
                    
                # 如果键名不同，更新键名（例如文件被重命名）
                if existing_key != key:
                    self.index.add_picture(key, pic)
                    self.index.remove_picture(existing_key)
            else:
                # 新文件，创建新的Picture对象
                new_pic = Picture(
                    path=filepath, 
                    relative_path=rel_path,
                    file_hash=file_hash,
                    display_name=filename
                )
                self.index.add_picture(key, new_pic)
        
        # 检测并删除已从文件系统中删除的文件
        keys_to_remove = set(self.index.get_all_keys()) - processed_keys
        for key in keys_to_remove:
            self.index.remove_picture(key)
        
        # 更新时间戳并保存
        self.index.update_timestamp()
        self.save_index()
        return True
    
    def load_index(self) -> bool:
        """加载索引文件"""
        if not os.path.exists(self.config.indexFile.value):
            self.index = WallpaperIndex()
            return False
            
        try:
            with open(self.config.indexFile.value, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.index = WallpaperIndex.from_dict(data)
            return True
        except Exception as e:
            print(f"加载索引失败: {e}")
            self.index = WallpaperIndex()
            return False
    
    def save_index(self) -> bool:
        """保存索引文件"""
        if not self.index.is_modified():
            return True  # 没有修改，不需要保存
            
        try:
            indexFile = self.config.indexFile.value
            # 确保目录存在
            os.makedirs(os.path.dirname(indexFile), exist_ok=True)
            
            # 先写入临时文件，成功后再替换
            temp_file = f"{indexFile}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.index.to_dict(), f, ensure_ascii=False, indent=2)
                
            # 原子替换原文件
            if os.path.exists(indexFile):
                os.replace(temp_file, indexFile)
            else:
                os.rename(temp_file, indexFile)
                
            self.index.mark_saved()
            return True
        except Exception as e:
            print(f"保存索引失败: {e}")
            return False
    
    def update_crop_region(self, key: str, crop_region: Dict[str, float], cache_filename: str = None) -> bool:
        """更新裁剪区域"""
        pic = self.index.get_picture(key)
        if pic:
            pic.update_crop(crop_region, cache_filename)
            return True
        return False
    
    def get_wallpaper_list(self, include_excluded: bool = True) -> List[str]:
        """获取壁纸列表"""
        if include_excluded:
            return self.index.get_all_keys()
        else:
            return self.index.get_filtered_keys(excluded=False)
    
    def get_excluded_list(self) -> List[str]:
        """获取排除的壁纸列表"""
        return self.index.get_filtered_keys(excluded=True)
    
    def set_excluded(self, key: str, excluded: bool) -> bool:
        """设置壁纸排除状态"""
        pic = self.index.get_picture(key)
        if pic:
            pic.set_excluded(excluded)
            return True
        return False
    
    def get_wallpaper_info(self, key: str) -> Dict[str, Any]:
        """获取壁纸信息"""
        pic = self.index.get_picture(key)
        if pic:
            return pic.to_dict()
        return {}
    
    def set_wallpaper(self, image_path: str, async_mode: bool = True) -> None:
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
    
    def get_thumbnail_base64(self, key: str) -> Optional[str]:
        """获取壁纸缩略图的base64编码，如果不存在则生成"""
        pic = self.index.get_picture(key)
        if not pic:
            return None
        
        # 如果已有缩略图，直接返回
        if pic.view_pic:
            return pic.view_pic
        
        # 否则生成缩略图
        thumbnail = self._create_thumbnail_base64(pic.path)
        if thumbnail:
            pic.set_thumbnail(thumbnail)
        
        return thumbnail
    
    def regenerate_thumbnail(self, key: str) -> Optional[str]:
        """重新生成缩略图"""
        pic = self.index.get_picture(key)
        if not pic:
            return None
            
        thumbnail = self._create_thumbnail_base64(pic.path)
        if thumbnail:
            pic.set_thumbnail(thumbnail)
            
        return thumbnail
    
    def search_wallpapers(self, query: str) -> List[str]:
        """按名称搜索壁纸"""
        return self.index.search_by_name(query)
    
    def cleanup_cache(self) -> int:
        """清理无效的缓存文件，返回清理的文件数量"""
        if not os.path.exists(self.config.cacheDir.value):
            return 0
            
        # 收集所有有效的缓存文件路径
        valid_cache_files = set()
        for pic in self.index.wallpapers.values():
            if pic.cache_path:
                valid_cache_files.add(pic.cache_path)
        
        # 删除无效的缓存文件
        deleted_count = 0
        for file in os.listdir(self.config.cacheDir.value):
            if file not in valid_cache_files:
                try:
                    os.remove(os.path.join(self.config.cacheDir.value, file))
                    deleted_count += 1
                except Exception as e:
                    print(f"删除缓存文件失败: {file}, 错误: {e}")
        
        return deleted_count