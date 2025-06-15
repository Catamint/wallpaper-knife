# 导入QFluentWidgets组件
from qfluentwidgets import (ConfigItem, QConfig, OptionsConfigItem, OptionsValidator, 
                          BoolValidator, FolderValidator)
import os
# 创建配置类
class WallpaperConfig(QConfig):
    """壁纸管理器配置"""

    # 常规设置
    autoStart = ConfigItem("App", "AutoStart", False, BoolValidator())
    randomOnStartup = ConfigItem("App", "RandomOnStartup", True, BoolValidator())
    
    # 目录设置
    wallpaperDir = ConfigItem("Directories", "WallpaperDir", "./wallpapers", FolderValidator())
    cacheDir = ConfigItem("Directories", "CacheDir", "./cache", FolderValidator())
    toolsDir = ConfigItem("Directories", "ToolsDir", "./tools", FolderValidator())
    
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
        # 主题设置
    defaultTheme = OptionsConfigItem(
        "App", "Theme", "light", 
        OptionsValidator(["light", "dark", "system"])
    )
    # 托盘设置
    minimizeOnAutoStart = ConfigItem("Tray", "MinimizeOnAutoStart", True, BoolValidator())
    minimizeOnClose = ConfigItem("Tray", "MinimizeOnClose", True, BoolValidator())

    def __init__(self):
        super().__init__()
        # 加载配置文件
        try:
            # 尝试加载配置文件
            if not os.path.exists("config.json"):
                # 如果配置文件不存在，使用默认设置
                self.save()
                print("配置文件不存在，已创建默认配置文件")
            else:
                # 加载现有配置文件
                self.load("config.json")
            print("成功加载配置文件")
        except Exception as e:
            print(f"加载配置文件出错: {e}")

# 创建全局配置实例
wallpaperCfg = WallpaperConfig()