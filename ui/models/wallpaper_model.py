from PyQt6.QtCore import QObject, pyqtSignal
import os

class WallpaperModel(QObject):
    """壁纸数据模型，管理数据并发送状态变化信号"""
    
    # 信号定义
    wallpapersChanged = pyqtSignal(list)
    currentWallpaperChanged = pyqtSignal(str, dict)  # filename, info
    indexingStarted = pyqtSignal()
    indexingProgress = pyqtSignal(int, int, str)  # current, total, filename
    indexingFinished = pyqtSignal(bool)  # success
    
    def __init__(self, wallpaper_manager, file_utils):
        super().__init__()
        self.manager = wallpaper_manager
        self.file_utils = file_utils
        
        # 数据缓存
        self.current_index = 0
        self.wallpaper_list = []
        
    def initialize(self):
        """初始化数据"""
        self._reload_wallpaper_list()
        
    def _reload_wallpaper_list(self):
        """重新加载壁纸列表 - 只加载未排除的壁纸"""
        all_wallpapers = self.manager.get_wallpaper_list()
        
        # 过滤出未排除的壁纸
        self.wallpaper_list = []
        for filename in all_wallpapers:
            wallpaper_info = self.manager.index_data["wallpapers"].get(filename, {})
            if not wallpaper_info.get("excluded", False):
                self.wallpaper_list.append(filename)
                
        self.wallpapersChanged.emit(self.wallpaper_list)
    
    def get_all_wallpapers(self):
        """获取所有壁纸信息 (包括已排除的)"""
        if not self.manager.index_data or "wallpapers" not in self.manager.index_data:
            return {}
        return self.manager.index_data["wallpapers"]
    
    def get_excluded_wallpapers(self):
        """获取所有已排除的壁纸文件名列表"""
        excluded_files = []
        for filename, info in self.get_all_wallpapers().items():
            if info.get("excluded", False):
                excluded_files.append(filename)
        return excluded_files
    
    def exclude_wallpaper(self, filename):
        """排除指定壁纸"""
        if filename not in self.manager.index_data["wallpapers"]:
            return False
            
        # 标记为已排除
        self.manager.index_data["wallpapers"][filename]["excluded"] = True
        # 保存索引
        self.manager.save_index()
        
        # 如果在当前列表中，则移除
        if filename in self.wallpaper_list:
            self.wallpaper_list.remove(filename)
            self.wallpapersChanged.emit(self.wallpaper_list)
        
        return True
    
    def include_wallpaper(self, filename):
        """恢复被排除的壁纸"""
        if filename not in self.manager.index_data["wallpapers"]:
            return False
            
        # 取消排除标记
        self.manager.index_data["wallpapers"][filename]["excluded"] = False
        # 保存索引
        self.manager.save_index()
        
        # 添加到当前列表
        if filename not in self.wallpaper_list:
            self.wallpaper_list.append(filename)
            self.wallpaper_list.sort()  # 保持顺序
            self.wallpapersChanged.emit(self.wallpaper_list)
        
        return True
    
    def exclude_current_wallpaper(self):
        """排除当前壁纸"""
        if not self.wallpaper_list:
            return False
            
        filename = self.wallpaper_list[self.current_index]
        result = self.exclude_wallpaper(filename)
        
        # 更新当前索引并发出信号
        if result and self.wallpaper_list:
            self.current_index = self.current_index % len(self.wallpaper_list)
            self.currentWallpaperChanged.emit(
                self.wallpaper_list[self.current_index], 
                self.manager.index_data["wallpapers"][self.wallpaper_list[self.current_index]]
            )
            
        return result
    
    def set_current_by_filename(self, filename):
        """根据文件名设置当前壁纸"""
        if filename in self.wallpaper_list:
            index = self.wallpaper_list.index(filename)
            return self.set_current_index(index)
        return False
    
    # 以下方法保持不变
    def load_index(self):
        """加载索引文件"""
        return self.manager.load_index()
    
    def need_rebuild_index(self):
        """检查是否需要重建索引"""
        return self.manager.need_rebuild_index() if hasattr(self.manager, 'need_rebuild_index') else False
    
    def build_index(self, progress_callback=None):
        """构建索引"""
        self.indexingStarted.emit()
        success = self.manager.build_index(progress_callback)
        self.indexingFinished.emit(success)
        if success:
            self._reload_wallpaper_list()
        return success
    
    def get_current_wallpaper(self):
        """获取当前壁纸信息"""
        if not self.wallpaper_list:
            return None, None
        filename = self.wallpaper_list[self.current_index]
        info = self.manager.index_data["wallpapers"][filename]
        return filename, info
    
    def set_current_index(self, index):
        """设置当前索引"""
        if not self.wallpaper_list:
            return False
        
        self.current_index = index % len(self.wallpaper_list)
        filename, info = self.get_current_wallpaper()
        if filename:
            self.currentWallpaperChanged.emit(filename, info)
            return True
        return False
    
    def next_wallpaper(self):
        """下一张壁纸"""
        if not self.wallpaper_list:
            return False
        return self.set_current_index(self.current_index + 1)
    
    def prev_wallpaper(self):
        """上一张壁纸"""
        if not self.wallpaper_list:
            return False
        return self.set_current_index(self.current_index - 1)
    
    def set_wallpaper(self, path, async_mode=True):
        """设置壁纸"""
        return self.manager.set_wallpaper(path, async_mode)
    
    def set_current_wallpaper(self):
        """设置当前壁纸"""
        if not self.wallpaper_list:
            return False
            
        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]
        
        # 优先使用缓存文件
        if wallpaper_info.get("cache_path") and wallpaper_info["cache_path"]:
            cache_path = os.path.join(self.manager.config.CACHE_DIR, wallpaper_info["cache_path"])
            if os.path.exists(cache_path):
                self.manager.set_wallpaper(cache_path)
                return True
        
        # 使用原图
        self.manager.set_wallpaper(wallpaper_info["path"])
        return True
    
    def update_crop_region(self, filename, crop_region, cache_filename=None):
        """更新裁剪区域"""
        self.manager.update_crop_region(filename, crop_region, cache_filename)