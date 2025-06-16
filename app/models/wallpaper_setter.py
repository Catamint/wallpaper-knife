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
from .picture_item import Picture
from app.utils.image_utils import ImageUtils  # 确保图像处理工具类已正确导入

class WallpaperSetter:
    """壁纸管理器"""
    def __init__(self):
        self.wallpaper_setter_thread = None
        self.wallpaper_setter_event = threading.Event()
    
    def set_wallpaper(self, picture_or_path: Union[Picture, str], async_mode: bool = True) -> bool:
        """设置壁纸，支持Picture对象或文件路径，可异步
        
        Args:
            picture_or_path: Picture对象或壁纸文件路径
            async_mode: 是否异步设置壁纸
            
        Returns:
            bool: 操作是否成功
        """
        # 确定实际路径
        image_path = self._get_path(picture_or_path)
        if not image_path or not os.path.exists(image_path):
            print(f"壁纸路径不存在: {image_path}")
            return False
            
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
                        print(f"壁纸已设置: {path}")
                        return True
                    except Exception as e:
                        print(f"设置壁纸失败: {e}")
                        return False
                return False

            self.wallpaper_setter_thread = threading.Thread(
                target=setter, args=(image_path, self.wallpaper_setter_event), daemon=True
            )
            self.wallpaper_setter_thread.start()
            return True  # 启动线程成功
        else:
            # 同步设置
            try:
                ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
                print(f"壁纸已设置: {image_path}")
                return True
            except Exception as e:
                print(f"设置壁纸失败: {e}")
                return False
    
    def _get_path(self, picture_or_path: Union[Picture, str]) -> str:
        """从Picture对象或路径字符串中获取实际文件路径
        
        Args:
            picture_or_path: Picture对象或壁纸文件路径
            
        Returns:
            str: 实际文件路径
        """
        if isinstance(picture_or_path, Picture):
            # 如果有裁剪的缓存文件，使用缓存文件
            if picture_or_path.cache_path and os.path.exists(picture_or_path.cache_path):
                return picture_or_path.cache_path
            # 否则使用原始文件
            return picture_or_path.path
        elif isinstance(picture_or_path, str):
            # 直接返回路径
            return picture_or_path
        else:
            print(f"不支持的壁纸类型: {type(picture_or_path)}")
            return ""
