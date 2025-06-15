import os
import datetime
from typing import Dict, List, Optional, Tuple, Callable, Any, Union

class Picture:
    """图片对象，封装图片的所有属性和处理方法"""
    
    def __init__(self, path: str, relative_path: str, file_hash: str, display_name: str = None):
        self.path = path
        self.relative_path = relative_path
        self.hash = file_hash
        self.display_name = display_name or os.path.basename(path)
        self.crop_region = None
        self.cache_path = None
        self.view_pic = None  # base64缩略图
        self.excluded = False
        self.last_accessed = datetime.datetime.now().isoformat()
        self.added_date = datetime.datetime.now().isoformat()
        self._modified = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Picture':
        """从字典创建Picture对象"""
        pic = cls(
            path=data.get("path", ""),
            relative_path=data.get("relative_path", ""),
            file_hash=data.get("hash", ""),
            display_name=data.get("display_name", "")
        )
        pic.crop_region = data.get("crop_region")
        pic.cache_path = data.get("cache_path")
        pic.view_pic = data.get("view_pic")
        pic.excluded = data.get("excluded", False)
        pic.last_accessed = data.get("last_accessed", pic.last_accessed)
        pic.added_date = data.get("added_date", pic.added_date)
        pic._modified = False
        return pic
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path": self.path,
            "relative_path": self.relative_path, 
            "hash": self.hash,
            "display_name": self.display_name,
            "crop_region": self.crop_region,
            "cache_path": self.cache_path,
            "view_pic": self.view_pic,
            "excluded": self.excluded,
            "last_accessed": self.last_accessed,
            "added_date": self.added_date
        }
    
    def update_path(self, new_path: str, new_relative_path: str) -> None:
        """更新路径"""
        self.path = new_path
        self.relative_path = new_relative_path
        self._modified = True
    
    def update_crop(self, crop_region: Dict[str, float], cache_path: str = None) -> None:
        """更新裁剪区域"""
        self.crop_region = crop_region
        if cache_path:
            self.cache_path = cache_path
        self._modified = True
    
    def set_thumbnail(self, thumbnail: str) -> None:
        """设置缩略图"""
        self.view_pic = thumbnail
        self._modified = True
    
    def clear_thumbnail(self) -> None:
        """清除缩略图"""
        self.view_pic = None
        self._modified = True
    
    def set_excluded(self, excluded: bool) -> None:
        """设置排除状态"""
        self.excluded = excluded
        self._modified = True
    
    def update_access_time(self) -> None:
        """更新访问时间"""
        self.last_accessed = datetime.datetime.now().isoformat()
        self._modified = True
    
    def is_modified(self) -> bool:
        """是否被修改过"""
        return self._modified
    
    def mark_saved(self) -> None:
        """标记为已保存"""
        self._modified = False