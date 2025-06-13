import os
import json
import sys
import traceback
from PyQt6.QtWidgets import QMessageBox

class Config:
    """应用程序配置类，支持从settings.json加载配置"""
    
    def __init__(self):
        try:
            # 基础目录设置
            self.BASE_DIR = self._get_base_dir()
            print(f"BASE_DIR: {self.BASE_DIR}")  # 添加调试日志
            
            # 默认配置
            self.default_settings = {
                "app": {
                    "name": "壁纸管理器",
                    "version": "1.0.0",
                    "ui_framework": "qt",
                    "language": "zh_CN",
                    "theme": "light",
                    "auto_start": False,
                    "random_on_startup": True,  # 启动时随机选择壁纸
                },
                "directories": {
                    "wallpaper": os.path.join(os.path.expanduser("~"), "Pictures", "Wallpapers"),
                    "cache": "wallpaper_cache",
                    "tools": "tools"
                },
                "files": {
                    "index": "wallpaper_index.json",
                    "excluded": "excluded.txt"
                },
                "realesrgan": {
                    "enabled": True,
                    "executable": "realesrgan\\realesrgan-ncnn-vulkan.exe",
                    "scale": 2,
                    "model": "realesrgan-x4plus"
                },
                "display": {
                    "wallpaper_change_interval": 0,
                    "show_notifications": True,
                    "enable_animations": True,
                    "random_interval": 0,       # 随机切换壁纸的间隔(分钟)，0表示禁用
                },
                "gallery": {
                    "thumbnail_size": 180,
                    "items_per_row": 0,
                    "default_sort": "filename",
                    "show_excluded": True
                }
            }
            
            # 加载设置
            self.settings = self.load_settings()
            
            # 设置属性
            self._setup_properties()
            
        except Exception as e:
            print(f"初始化配置时发生错误: {str(e)}")
            traceback.print_exc()
            self._show_error(f"初始化配置失败: {str(e)}")
            # 设置基本配置避免程序崩溃
            self._setup_emergency_config()
    
    def _get_base_dir(self):
        """获取应用程序基础目录"""
        if getattr(sys, 'frozen', False):
            # 如果是打包环境（PyInstaller）
            base_dir = os.path.dirname(sys.executable)
            print(f"运行在打包环境: {base_dir}")
            return base_dir
        else:
            # 开发环境
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            print(f"运行在开发环境: {base_dir}")
            return base_dir
    
    def _show_error(self, message):
        """显示错误消息"""
        try:
            # 尝试使用Qt显示错误
            if 'PyQt6.QtWidgets' in sys.modules:
                try:
                    from PyQt6.QtWidgets import QApplication
                    if not QApplication.instance():
                        app = QApplication([])
                    QMessageBox.critical(None, "配置错误", message)
                except:
                    print(f"错误: {message}")
        except:
            # 如果无法使用GUI，输出到控制台
            print(f"错误: {message}")
            
    def _setup_emergency_config(self):
        """设置紧急配置以避免程序崩溃"""
        # 基本目录设置
        self.WALLPAPER_DIR = os.path.join(self.BASE_DIR, "wallpapers")
        self.CACHE_DIR = os.path.join(self.BASE_DIR, "cache")
        self.TOOLS_DIR = os.path.join(self.BASE_DIR, "tools")
        self.INDEX_FILE = os.path.join(self.BASE_DIR, "wallpaper_index.json")
        self.EXCLUDE_FILE = os.path.join(self.BASE_DIR, "excluded.txt")
        
        # 确保目录存在
        os.makedirs(self.WALLPAPER_DIR, exist_ok=True)
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        
        # 基本设置
        self.THEME = "light"
        self.THUMBNAIL_SIZE = 180
        
        # 创建默认设置文件
        self.save_settings(self.default_settings)
        
    def load_settings(self):
        """从settings.json加载设置"""
        settings_file = os.path.join(self.BASE_DIR, "settings.json")
        settings = self.default_settings.copy()
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                # 递归更新设置，保留默认值
                settings = self._deep_update(settings, loaded_settings)
            else:
                # 如果文件不存在，创建默认设置文件
                self.save_settings(settings)
                
        except Exception as e:
            error_msg = f"加载设置文件失败: {str(e)}\n使用默认设置。"
            print(error_msg)
            
            # 在GUI环境中显示错误
            if 'PyQt6' in sys.modules:
                try:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(None, "设置加载错误", error_msg)
                except:
                    pass
        
        return settings
    
    def save_settings(self, settings=None):
        """保存设置到settings.json"""
        if settings is None:
            settings = self.settings
            
        settings_file = os.path.join(self.BASE_DIR, "settings.json")
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            error_msg = f"保存设置文件失败: {str(e)}"
            print(error_msg)
            
            # 在GUI环境中显示错误
            if 'PyQt6' in sys.modules:
                try:
                    QMessageBox.warning(None, "设置保存错误", error_msg)
                except:
                    pass
            return False
    
    def _deep_update(self, d, u):
        """递归更新嵌套字典，保留原始键"""
        import copy
        result = copy.deepcopy(d)
        
        for k, v in u.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = self._deep_update(result[k], v)
            else:
                result[k] = copy.deepcopy(v)
        return result
    
    def _setup_properties(self):
        """根据加载的设置设置类属性"""
        # 应用程序设置
        self.APP_NAME = self.settings["app"]["name"]
        self.APP_VERSION = self.settings["app"]["version"]
        self.UI = self.settings["app"]["ui_framework"]
        self.LANGUAGE = self.settings["app"]["language"]
        self.THEME = self.settings["app"]["theme"]
        self.AUTO_START = self.settings["app"]["auto_start"]
        
        # 目录设置
        wallpaper_dir = self.settings["directories"]["wallpaper"]
        if not os.path.isabs(wallpaper_dir):
            wallpaper_dir = os.path.join(self.BASE_DIR, wallpaper_dir)
            
        self.WALLPAPER_DIR = wallpaper_dir
        
        cache_dir = self.settings["directories"]["cache"]
        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(self.BASE_DIR, cache_dir)
            
        self.CACHE_DIR = cache_dir
        
        tools_dir = self.settings["directories"]["tools"]
        if not os.path.isabs(tools_dir):
            tools_dir = os.path.join(self.BASE_DIR, tools_dir)
            
        self.TOOLS_DIR = tools_dir
        
        # 文件设置
        index_file = self.settings["files"]["index"]
        if not os.path.isabs(index_file):
            index_file = os.path.join(self.BASE_DIR, index_file)
            
        self.INDEX_FILE = index_file
        
        exclude_file = self.settings["files"]["excluded"]
        if not os.path.isabs(exclude_file):
            exclude_file = os.path.join(self.BASE_DIR, exclude_file)
            
        self.EXCLUDE_FILE = exclude_file
        
        # Realesrgan 设置
        self.REALESRGAN_ENABLED = self.settings["realesrgan"]["enabled"]
        
        realesrgan_path = self.settings["realesrgan"]["executable"]
        if not os.path.isabs(realesrgan_path):
            realesrgan_path = os.path.join(self.TOOLS_DIR, realesrgan_path)
            
        self.REALESRGAN_PATH = realesrgan_path
        self.REALESRGAN_SCALE = self.settings["realesrgan"]["scale"]
        self.REALESRGAN_MODEL = self.settings["realesrgan"]["model"]
        
        # 显示设置
        self.WALLPAPER_CHANGE_INTERVAL = self.settings["display"]["wallpaper_change_interval"]
        self.SHOW_NOTIFICATIONS = self.settings["display"]["show_notifications"]
        self.ENABLE_ANIMATIONS = self.settings["display"]["enable_animations"]
        
        # 图库设置
        self.THUMBNAIL_SIZE = self.settings["gallery"]["thumbnail_size"]
        self.ITEMS_PER_ROW = self.settings["gallery"]["items_per_row"]
        self.DEFAULT_SORT = self.settings["gallery"]["default_sort"]
        self.SHOW_EXCLUDED = self.settings["gallery"]["show_excluded"]
        
        # 确保必要目录存在
        os.makedirs(self.WALLPAPER_DIR, exist_ok=True)
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        os.makedirs(self.TOOLS_DIR, exist_ok=True)
    
    def update_setting(self, section, key, value):
        """更新特定设置并保存"""
        if section in self.settings and key in self.settings[section]:
            self.settings[section][key] = value
            
            # 更新对应的属性
            attr_name = f"{section.upper()}_{key.upper()}"
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)
                
            # 重新设置属性
            self._setup_properties()
            
            # 保存设置
            return self.save_settings()
        return False