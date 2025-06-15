# 导入QFluentWidgets组件
from qfluentwidgets import (ConfigItem, QConfig, OptionsConfigItem, OptionsValidator, 
                          BoolValidator, FolderValidator, Theme, EnumSerializer)
import os
from pathlib import Path
from ..config import *

# 创建配置类
class WallpaperConfig(QConfig):
    """壁纸管理器配置"""

    # 常规设置
    defaultTheme = OptionsConfigItem(
        "App", "ThemeMode", "system",
        OptionsValidator(Theme), EnumSerializer(Theme)
    )
    autoStart = ConfigItem("App", "AutoStart", False, BoolValidator())
    randomOnStartup = ConfigItem("App", "RandomOnStartup", True, BoolValidator())
    wallpaperChangeInterval = ConfigItem(
        "App", "WallpaperChangeInterval", 
        DEFAULT_ROTATION_INTERVAL, 
        None
    )
    # 目录设置
    wallpaperDir = ConfigItem("Directories", "WallpaperDir", WALLPAPER_DIR, FolderValidator())
    cacheDir = ConfigItem("Directories", "CacheDir", CACHE_DIR, FolderValidator())
    toolsDir = ConfigItem("Directories", "ToolsDir", TOOLS_DIR, FolderValidator())
    indexFile = ConfigItem("Directories", "IndexFile", INDEX_FILE, None)

    # 显示设置
    notifications = ConfigItem("Display", "ShowNotifications", True, BoolValidator())
    animations = ConfigItem("Display", "EnableAnimations", True, BoolValidator())
    
    # Real-ESRGAN设置
    realesrganEnabled = ConfigItem("RealESRGAN", "Enabled", False, BoolValidator())
    realesrganPath = ConfigItem("RealESRGAN", "ExecutablePath", "", None)
    realesrganScale = OptionsConfigItem(
        "RealESRGAN", "Scale", 2, 
        OptionsValidator([2, 3, 4])
    )
    realesrganModel = OptionsConfigItem(
        "RealESRGAN", "Model", "realesrgan-x4plus", 
        OptionsValidator(["realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrnet-x4plus"])
    )
    # 托盘设置
    minimizeOnAutoStart = ConfigItem("Tray", "MinimizeOnAutoStart", True, BoolValidator())
    minimizeOnClose = ConfigItem("Tray", "MinimizeOnClose", True, BoolValidator())

    def __init__(self):
        super().__init__()
        self.file = Path(CONFIG_FILE)

        # 加载配置文件
        try:
            # 尝试加载配置文件
            if not os.path.exists(CONFIG_FILE):
                # 如果配置文件不存在，使用默认设置
                # wallpaperCfg.save()
                print("配置文件不存在，已创建默认配置文件")
            else:
                # 加载现有配置文件
                self.load(Path(CONFIG_FILE))
            print("成功加载配置文件")
        except Exception as e:
            print(f"加载配置文件出错: {e}")

    def __str__(self):
        return self.toDict().__str__()

# 创建全局配置实例
wallpaperCfg = WallpaperConfig()
