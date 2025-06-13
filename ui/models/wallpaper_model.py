from PyQt6.QtCore import QObject, pyqtSignal
import random
import os
from core.manager import WallpaperManager

class WallpaperModel(QObject):
    """壁纸数据模型，管理业务逻辑和应用状态，发送状态变化信号"""
    
    # 信号定义
    wallpapersChanged = pyqtSignal(list)  # 壁纸列表变化
    currentWallpaperChanged = pyqtSignal(str, dict)  # filename, info
    indexingStarted = pyqtSignal()  # 索引开始构建
    indexingProgress = pyqtSignal(int, int, str)  # current, total, filename
    indexingFinished = pyqtSignal(bool)  # success
    
    def __init__(self, wallpaper_manager):
        super().__init__()
        self.manager = wallpaper_manager
        
        # 应用状态
        self.current_key = None  # 当前壁纸键
        self.filtered_keys = []  # 过滤后的键列表
        self.view_settings = {
            "show_excluded": False,
            "sort_by": "filename", 
            "filter": ""
        }
    
    def _update_filtered_keys(self):
        """更新过滤后的键列表 - 根据视图设置过滤并排序"""
        # 根据是否显示排除的壁纸获取基础列表
        if self.view_settings["show_excluded"]:
            keys = self.manager.index.get_all_keys()
        else:
            keys = self.manager.index.get_filtered_keys(excluded=False)
        
        # 应用搜索过滤
        if self.view_settings["filter"]:
            query = self.view_settings["filter"].lower()
            filtered_keys = []
            for key in keys:
                pic = self.manager.index.get_picture(key)
                if pic and (query in pic.display_name.lower() or query in pic.path.lower()):
                    filtered_keys.append(key)
            keys = filtered_keys
        
        # 应用排序
        sort_by = self.view_settings["sort_by"]
        if sort_by == "filename":
            # 按文件名排序
            keys.sort(key=lambda k: self.manager.index.get_picture(k).display_name.lower())
        elif sort_by == "date":
            # 按添加日期排序
            keys.sort(key=lambda k: self.manager.index.get_picture(k).added_date)
        elif sort_by == "access":
            # 按最近访问排序
            keys.sort(key=lambda k: self.manager.index.get_picture(k).last_accessed, reverse=True)
        
        # 更新过滤后的列表
        old_keys = self.filtered_keys
        self.filtered_keys = keys
        
        # 如果键列表变化了，发出信号
        if old_keys != self.filtered_keys:
            self.wallpapersChanged.emit(self.filtered_keys)
        
        # 更新当前键的索引位置
        if self.current_key and self.current_key not in self.filtered_keys and self.filtered_keys:
            # 当前键不在过滤后的列表中，重置为第一个
            self.set_current_key(self.filtered_keys[0])
        elif not self.current_key and self.filtered_keys:
            # 没有当前键但有数据，设置为第一个
            self.set_current_key(self.filtered_keys[0])
        elif not self.filtered_keys:
            # 列表为空，清除当前键
            self.current_key = None
            self._notify_current_changed()
    
    def set_view_settings(self, **kwargs):
        """设置视图参数"""
        settings_changed = False
        
        for key, value in kwargs.items():
            if key in self.view_settings and self.view_settings[key] != value:
                self.view_settings[key] = value
                settings_changed = True
        
        # 只有在设置实际变化时才更新
        if settings_changed:
            self._update_filtered_keys()
    
    def get_all_wallpapers(self):
        """获取所有壁纸信息 (包括已排除的)"""
        result = {}
        for key in self.manager.index.get_all_keys():
            pic = self.manager.index.get_picture(key)
            if pic:
                result[key] = pic.to_dict()
        return result
    
    def get_excluded_wallpapers(self):
        """获取所有已排除的壁纸键列表"""
        return self.manager.index.get_filtered_keys(excluded=True)
    
    def exclude_wallpaper(self, key):
        """排除指定壁纸"""
        pic = self.manager.index.get_picture(key)
        if not pic:
            return False
            
        pic.set_excluded(True)
        # 保存更改
        self.manager.save_index()
        
        # 如果当前设置不显示已排除壁纸，需要更新过滤列表
        if not self.view_settings["show_excluded"]:
            self._update_filtered_keys()
            
        return True
    
    def include_wallpaper(self, key):
        """恢复被排除的壁纸"""
        pic = self.manager.index.get_picture(key)
        if not pic:
            return False
            
        pic.set_excluded(False)
        # 保存更改
        self.manager.save_index()
        
        # 如果当前设置不显示已排除壁纸，需要更新过滤列表
        if not self.view_settings["show_excluded"]:
            self._update_filtered_keys()
            
        return True
    
    def exclude_current_wallpaper(self):
        """排除当前壁纸"""
        if not self.current_key:
            return False
            
        return self.exclude_wallpaper(self.current_key)
    
    def set_current_key(self, key):
        """设置当前壁纸键"""
        if key not in self.manager.index.wallpapers:
            return False
            
        old_key = self.current_key
        self.current_key = key
        
        if old_key != self.current_key:
            self._notify_current_changed()
            
        return True
    
    def set_current_by_index(self, index):
        """根据索引位置设置当前壁纸"""
        if not self.filtered_keys:
            return False
            
        # 循环索引处理
        if index < 0:
            index = len(self.filtered_keys) - 1
        elif index >= len(self.filtered_keys):
            index = 0
            
        return self.set_current_key(self.filtered_keys[index])
    
    def get_current_index(self):
        """获取当前壁纸在过滤列表中的索引"""
        if not self.current_key or not self.filtered_keys:
            return -1
        try:
            return self.filtered_keys.index(self.current_key)
        except ValueError:
            return -1
    
    def next_wallpaper(self):
        """下一张壁纸"""
        current_index = self.get_current_index()
        if current_index == -1:
            # 当前无选中，选择第一张
            return self.set_current_by_index(0)
        return self.set_current_by_index(current_index + 1)
    
    def prev_wallpaper(self):
        """上一张壁纸"""
        current_index = self.get_current_index()
        if current_index == -1:
            # 当前无选中，选择最后一张
            return self.set_current_by_index(-1)
        return self.set_current_by_index(current_index - 1)
    
    def load_index(self):
        """加载索引文件"""
        result = self.manager.load_index()
        if result:
            self._update_filtered_keys()
        return result
    
    def build_index(self):
        """构建索引"""
        self.indexingStarted.emit()
        
        # 创建进度回调函数
        def progress_callback(current, total, filename):
            self.indexingProgress.emit(current, total, filename)
        
        # 调用管理器构建索引
        success = self.manager.build_index(progress_callback)
        
        # 完成后发出信号并更新列表
        self.indexingFinished.emit(success)
        if success:
            self._update_filtered_keys()
        
        return success
    
    def get_current_wallpaper(self):
        """获取当前壁纸信息"""
        if not self.current_key:
            return None, None
            
        pic = self.manager.index.get_picture(self.current_key)
        if not pic:
            return None, None
            
        return self.current_key, pic.to_dict()
    
    def _notify_current_changed(self):
        """通知当前壁纸变化"""
        key, info = self.get_current_wallpaper()
        if key:
            self.currentWallpaperChanged.emit(key, info)
    
    def set_wallpaper(self, path, async_mode=True):
        """设置壁纸"""
        return self.manager.set_wallpaper(path, async_mode)
    
    def set_current_wallpaper(self):
        """设置当前壁纸"""
        if not self.current_key:
            return False
            
        pic = self.manager.index.get_picture(self.current_key)
        if not pic:
            return False
        
        # 优先使用缓存文件
        if pic.cache_path:
            cache_path = os.path.join(self.manager.config.CACHE_DIR, pic.cache_path)
            if os.path.exists(cache_path):
                self.manager.set_wallpaper(cache_path)
                return True
        
        # 使用原图
        self.manager.set_wallpaper(pic.path)
        return True
    
    def update_crop_region(self, key, crop_region, cache_filename=None):
        """更新裁剪区域"""
        pic = self.manager.index.get_picture(key)
        if not pic:
            return False
            
        pic.update_crop(crop_region, cache_filename)
        # 保存更改
        self.manager.save_index()
        
        # 如果是当前壁纸，通知变化
        if key == self.current_key:
            self._notify_current_changed()
            
        return True
    
    def get_thumbnail(self, key):
        """获取缩略图"""
        pic = self.manager.index.get_picture(key)
        if not pic:
            return None
            
        # 如果已有缩略图
        if pic.view_pic:
            return pic.view_pic
            
        # 生成缩略图
        thumb = self.manager._create_thumbnail_base64(pic.path)
        if thumb:
            pic.set_thumbnail(thumb)
            # 异步保存索引（避免频繁保存）
            self.manager.save_index()
            
        return thumb
    
    def get_random_key(self):
        """获取随机键，不同于当前键"""
        if not self.filtered_keys:
            return None
            
        if len(self.filtered_keys) == 1:
            return self.filtered_keys[0]
            
        available = self.filtered_keys.copy()
        if self.current_key in available:
            available.remove(self.current_key)
            
        if not available:
            return None
            
        return random.choice(available)
        
    def random_wallpaper(self):
        """选择一个随机壁纸"""
        random_key = self.get_random_key()
        if random_key:
            return self.set_current_key(random_key)
        return False
    
    def cleanup_cache(self):
        """清理无效缓存"""
        return self.manager.cleanup_cache()
    
    def get_wallpaper_count(self):
        """获取当前过滤条件下的壁纸数量"""
        return len(self.filtered_keys)
    
    def get_total_count(self):
        """获取壁纸总数"""
        return self.manager.index.total_count