import time, json
import threading, os
import base64
from PIL import Image  # 使用 Pillow 处理图像
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from .picture_item import Picture
from app.utils.image_utils import ImageUtils  # 确保图像处理工具类已正确导入

from .settings import wallpaperCfg # 确保配置类已正确导入
from app.models.wallpaper_setter import WallpaperSetter

setter = WallpaperSetter()

class IndexManager:
    """壁纸索引管理类"""
    
    def __init__(self):
        self.picture_index: Dict[str, Picture] = {}
        self.current_key: Optional[str] = None
        self.total_count: int = 0
        self.last_updated: Optional[float] = None
        self._modified: bool = False
        self.auto_save_timer = None
        self._start_auto_save()

    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典创建索引"""
        self.picture_index = {
            k: Picture.from_dict(v) if isinstance(v, dict) else v 
            for k, v in data.get("wallpapers", {}).items()
        }
        self.total_count = data.get("total_count", len(self.picture_index))
        self.last_updated = data.get("last_updated")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "wallpapers": {k: v.to_dict() for k, v in self.picture_index.items()},
            "current_key": self.current_key,
            "total_count": self.total_count,
            "last_updated": self.last_updated
        }
    
    def load_index(self) -> bool:
        """加载索引文件"""
        if not os.path.exists(wallpaperCfg.indexFile.value):
            print("索引文件不存在，无法加载")
            return False
            
        try:
            with open(wallpaperCfg.indexFile.value, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.from_dict(data)
            return True
        except Exception as e:
            print(f"加载索引失败: {e}")
            return False
        
    def add_picture(self, picture: Picture) -> str:
        """添加图片，返回生成的键"""
        key = self.get_key_for_picture(picture)
        self.picture_index[key] = picture
        self._modified = True
        self.recount()
        return key
    
    def remove_picture(self, picture_or_key: Union[Picture, str]) -> bool:
        """删除图片"""
        if isinstance(picture_or_key, Picture):
            # 查找图片对应的键
            for key, pic in self.picture_index.items():
                if pic is picture_or_key:
                    del self.picture_index[key]
                    self._modified = True
                    self.recount()
                    return True
            return False
        else:
            key = picture_or_key
            if key in self.picture_index:
                del self.picture_index[key]
                self._modified = True
                self.recount()
                return True
            return False
    
    def get_picture(self, key: str) -> Optional[Picture]:
        """获取图片"""
        pic = self.picture_index.get(key)
        if pic:
            pic.update_access_time()
        return pic
    
    def get_picture_by_hash(self, hash_value: str) -> Optional[Picture]:
        """通过哈希值获取图片"""
        for pic in self.picture_index.values():
            if pic.hash == hash_value:
                pic.update_access_time()
                return pic
        return None
    
    def get_key_for_picture(self, picture: Picture) -> Optional[str]:
        """获取图片对应的键"""
        return self._generate_key_from_file(picture.hash, os.path.basename(picture.path))
    
    def get_all_keys(self) -> List[str]:
        """获取所有键"""
        return list(self.picture_index.keys())
    
    def get_all_pictures(self) -> List[Picture]:
        """获取所有图片对象"""
        return list(self.picture_index.values())
    
    def get_filtered_keys(self, excluded: bool = False) -> List[str]:
        """获取过滤后的键列表"""
        return [k for k, v in self.picture_index.items() if v.excluded == excluded]
    
    def get_filtered_pictures(self, excluded: bool = False) -> List[Picture]:
        """获取过滤后的图片对象列表"""
        return [v for v in self.picture_index.values() if v.excluded == excluded]
    
    def search_by_name(self, query: str) -> List[Picture]:
        """按名称搜索，返回图片对象列表"""
        query = query.lower()
        return [v for v in self.picture_index.values() 
                if query in v.display_name.lower() or query in v.path.lower()]
    
    def search_by_hash(self, hash_value: str) -> Optional[Picture]:
        """按哈希值搜索，返回图片对象"""
        for pic in self.picture_index.values():
            if pic.hash == hash_value:
                return pic
        return None
    
    def recount(self) -> None:
        """重新计数"""
        self.total_count = len(self.picture_index)
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
        for pic in self.picture_index.values():
            if pic.is_modified():
                return True
        
        return False
    
    def mark_saved(self) -> None:
        """标记为已保存"""
        self._modified = False
        for pic in self.picture_index.values():
            pic.mark_saved()

    def clear(self) -> None:
        """清空索引"""
        self.picture_index.clear()
        self.total_count = 0
        self.last_updated = None
        self._modified = False
        
    def _start_auto_save(self, interval: int = 300) -> None:
        """启动自动保存定时器"""
        def auto_save():
            while True:
                time.sleep(interval)
                if self.is_modified():
                    self.save()
        
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
        if not os.path.exists(wallpaperCfg.wallpaperDir.value):
            return False
            
        # 先加载现有索引
        self.load_index()
        
        # 暂存已知文件的哈希值，用于快速查找
        existing_hashes = {pic.hash: key for key, pic in self.picture_index.items()}
        
        # 扫描文件系统
        image_files = []
        for root, _, files in os.walk(wallpaperCfg.wallpaperDir.value):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, wallpaperCfg.wallpaperDir.value)
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
                pic = self.get_picture(existing_key)
                
                # 路径可能有变化
                if pic.path != filepath:
                    pic.update_path(filepath, rel_path)
                    
                # 如果键名不同，更新键名（例如文件被重命名）
                if existing_key != key:
                    self.picture_index[key] = pic
                    del self.picture_index[existing_key]
                    self._modified = True
            else:
                # 新文件，创建新的Picture对象
                new_pic = Picture(
                    path=filepath, 
                    relative_path=rel_path,
                    file_hash=file_hash,
                    display_name=filename
                )
                self.picture_index[key] = new_pic
                self._modified = True
        
        # 检测并删除已从文件系统中删除的文件
        keys_to_remove = set(self.get_all_keys()) - processed_keys
        for key in keys_to_remove:
            self.remove_picture(key)
        
        # 更新时间戳并保存
        self.recount()
        self.update_timestamp()
        self.save()
        return True
    
    def save(self) -> bool:
        """保存索引文件"""
        if not self.is_modified():
            return True  # 没有修改，不需要保存
            
        try:
            indexFile = wallpaperCfg.indexFile.value
            # 确保目录存在
            os.makedirs(os.path.dirname(indexFile), exist_ok=True)
            
            # 先写入临时文件，成功后再替换
            temp_file = f"{indexFile}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

            # 原子替换原文件
            if os.path.exists(indexFile):
                os.replace(temp_file, indexFile)
            else:
                os.rename(temp_file, indexFile)
                
            self.mark_saved()
            return True
        except Exception as e:
            print(f"保存索引失败: {e}")
            return False
    
    def get_thumbnail_base64(self, picture_or_key: Union[Picture, str]) -> Optional[str]:
        """获取壁纸缩略图的base64编码，如果不存在则生成"""
        pic = None
        if isinstance(picture_or_key, Picture):
            pic = picture_or_key
        else:
            pic = self.get_picture(picture_or_key)
            
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
    
    def regenerate_thumbnail(self, picture_or_key: Union[Picture, str]) -> Optional[str]:
        """重新生成缩略图"""
        pic = None
        if isinstance(picture_or_key, Picture):
            pic = picture_or_key
        else:
            pic = self.get_picture(picture_or_key)
            
        if not pic:
            return None
            
        thumbnail = self._create_thumbnail_base64(pic.path)
        if thumbnail:
            pic.set_thumbnail(thumbnail)
            
        return thumbnail
    
    def cleanup_cache(self) -> int:
        """清理无效的缓存文件，返回清理的文件数量"""
        if not os.path.exists(wallpaperCfg.cacheDir.value):
            return 0
            
        # 收集所有有效的缓存文件路径
        valid_cache_files = set()
        for pic in self.picture_index.values():
            if pic.cache_path:
                valid_cache_files.add(pic.cache_path)
        
        # 删除无效的缓存文件
        deleted_count = 0
        for file in os.listdir(wallpaperCfg.cacheDir.value):
            if file not in valid_cache_files:
                try:
                    os.remove(os.path.join(wallpaperCfg.cacheDir.value, file))
                    deleted_count += 1
                except Exception as e:
                    print(f"删除缓存文件失败: {file}, 错误: {e}")
        
        return deleted_count
    
    def set_excluded(self, picture_or_key: Union[Picture, str], excluded: bool) -> bool:
        """设置壁纸排除状态"""
        pic = None
        if isinstance(picture_or_key, Picture):
            pic = picture_or_key
        else:
            pic = self.get_picture(picture_or_key)
            
        if pic:
            pic.set_excluded(excluded)
            return True
        return False
    
    def set_wallpaper(self, picture_or_key: Union[Picture, str], async_mode: bool = True) -> bool:
        """设置壁纸"""
        pic = None
        if isinstance(picture_or_key, Picture):
            pic = picture_or_key
        else:
            pic = self.get_picture(picture_or_key)
        
        if not pic:
            print("指定的壁纸不存在")
            return False
        
        try:
            setter.set_wallpaper(pic.path, async_mode)     
            self.current_key = pic.get_key()
            return True
        except Exception as e:
            print(f"设置壁纸失败: {e}")
            return False