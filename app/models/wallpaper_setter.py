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
