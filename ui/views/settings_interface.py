from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
                            QPushButton, QScrollArea, QComboBox, QLineEdit, QCheckBox,
                            QToolButton, QGridLayout, QSpinBox, QFileDialog, QGroupBox, QFormLayout,
                            QTabWidget)

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentWindow, FluentIcon as FIF, NavigationItemPosition,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, TitleLabel, SubtitleLabel, CaptionLabel, 
                          setTheme, Theme, InfoBar, InfoBarPosition, CardWidget, 
                          ScrollArea, ExpandLayout, SettingCardGroup, SwitchSettingCard,
                          ComboBoxSettingCard, PushSettingCard, LineEdit, 
                          ConfigItem, QConfig, OptionsConfigItem, OptionsValidator, 
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
    # toolsDir = ConfigItem("Directories", "ToolsDir", "./tools", FolderValidator())
    
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


class SettingsInterface(QFrame):
    """设置界面 - 使用信号机制实时修改设置"""
    
    # 定义信号
    settingsChanged = pyqtSignal()  # 当设置改变时发出信号
    
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller
        self.setObjectName("Settings-Interface")
        
        # 设置透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 使用QConfig配置
        self.config = wallpaperCfg
        
        # 初始化UI
        self.setup_ui()
        self._connect_signals()
        
        # 从应用配置同步设置
        self.sync_from_app_config()
    
    def setup_ui(self):
        """设置设置界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title_label = TitleLabel("设置")
        main_layout.addWidget(title_label)
        
        # 创建滚动区域
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setObjectName("settingsScrollArea")
        
        # 设置滚动区域为透明
        self.scroll_area.setStyleSheet("""
            QScrollArea#settingsScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea#settingsScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)
        
        # 创建滚动内容
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("settingsContent")
        
        # 设置滚动内容为透明
        self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_content.setStyleSheet("#settingsContent { background-color: transparent; }")
        
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)
        
        # 创建各个设置组
        self.create_general_group()
        self.create_directory_group()
        self.create_display_group()
        self.create_realesrgan_group()
        
        # 添加弹性空间
        self.scroll_layout.addStretch(1)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, 1)
    
    def _connect_signals(self):
        """连接所有设置项的信号"""
        # 主题设置
        self.config.defaultTheme.valueChanged.connect(self._on_theme_changed)
        
        # 开机自启和其他开关设置
        self.config.autoStart.valueChanged.connect(self._on_auto_start_changed)
        self.config.randomOnStartup.valueChanged.connect(self._notify_settings_changed)
        self.config.minimizeOnAutoStart.valueChanged.connect(self._notify_settings_changed)
        self.config.minimizeOnClose.valueChanged.connect(self._notify_settings_changed)
        
        # 显示设置
        self.config.notifications.valueChanged.connect(self._notify_settings_changed)
        self.config.animations.valueChanged.connect(self._notify_settings_changed)
        
        # Real-ESRGAN设置
        self.config.realesrganEnabled.valueChanged.connect(self._notify_settings_changed)
        self.config.realesrganScale.valueChanged.connect(self._notify_settings_changed)
        self.config.realesrganModel.valueChanged.connect(self._notify_settings_changed)
    
    def _on_theme_changed(self, theme):
        """主题改变时的处理"""
        # 应用主题
        if theme == "light":
            setTheme(Theme.LIGHT)
        elif theme == "dark":
            setTheme(Theme.DARK)
        else:  # system
            # 根据系统设置判断
            import darkdetect
            if darkdetect.isDark():
                setTheme(Theme.DARK)
            else:
                setTheme(Theme.LIGHT)
        
        self._notify_settings_changed()
    
    def _on_auto_start_changed(self, enabled):
        """自启动设置改变时的处理"""
        if hasattr(self.controller, 'set_auto_start'):
            self.controller.set_auto_start(enabled)
        self._notify_settings_changed()
    
    def _on_wallpaper_dir_changed(self, folder):
        """壁纸目录改变时的处理"""
        self.config.wallpaperDir.value = folder
        self._notify_settings_changed()
    
    def _on_cache_dir_changed(self, folder):
        """缓存目录改变时的处理"""
        self.config.cacheDir.value = folder
        self._notify_settings_changed()
    
    # def _on_tools_dir_changed(self, folder):
    #     """工具目录改变时的处理"""
    #     self.config.toolsDir.value = folder
    #     self._notify_settings_changed()
    
    def _on_realesrgan_path_changed(self, path):
        """Real-ESRGAN路径改变时的处理"""
        self.config.realesrganPath.value = path
        self._notify_settings_changed()
    
    def _notify_settings_changed(self):
        """通知设置已改变"""
        try:
            # 保存设置到配置文件
            self.config.save()
            
            # 应用设置到应用程序
            self._apply_settings_to_app()
            
            # 发出设置已更改信号
            self.settingsChanged.emit()
            
        except Exception as e:
            import traceback
            print(f"保存设置时发生错误: {e}")
            print(traceback.format_exc())
            self.show_error(f"保存设置时出错: {str(e)}")
    
    def _apply_settings_to_app(self):
        """将QConfig设置应用到应用程序"""
        try:
            app_config = self.controller.model.manager.config
            
            # 1. 同步应用基本配置
            app_config.settings["app"]["theme"] = self.config.defaultTheme.value
            app_config.settings["app"]["auto_start"] = self.config.autoStart.value
            app_config.settings["app"]["random_on_startup"] = self.config.randomOnStartup.value
            
            # 2. 同步目录配置
            app_config.settings["directories"]["wallpaper"] = self.config.wallpaperDir.value
            app_config.settings["directories"]["cache"] = self.config.cacheDir.value
            # app_config.settings["directories"]["tools"] = self.config.toolsDir.value
            
            # 3. 同步显示设置
            app_config.settings["display"]["show_notifications"] = self.config.notifications.value
            app_config.settings["display"]["enable_animations"] = self.config.animations.value
            
            # 4. 同步Real-ESRGAN设置
            app_config.settings["realesrgan"]["enabled"] = self.config.realesrganEnabled.value
            app_config.settings["realesrgan"]["executable"] = self.config.realesrganPath.value
            app_config.settings["realesrgan"]["scale"] = self.config.realesrganScale.value
            app_config.settings["realesrgan"]["model"] = self.config.realesrganModel.value
            
            # 5. 同步托盘设置
            if "tray" not in app_config.settings:
                app_config.settings["tray"] = {}
            app_config.settings["tray"]["minimize_on_auto_start"] = self.config.minimizeOnAutoStart.value
            app_config.settings["tray"]["minimize_on_close"] = self.config.minimizeOnClose.value
            
            # 6. 保存到文件
            app_config.save_settings()
            
            # 7. 更新内存中的属性
            app_config._setup_properties()
            
        except Exception as e:
            print(f"应用设置时出错: {e}")

    def sync_from_app_config(self):
        """从应用配置同步到QConfig"""
        try:
            app_config = self.controller.model.manager.config
            
            # 同步主题
            self.config.defaultTheme.value = app_config.THEME
            
            # 同步开关项
            self.config.autoStart.value = app_config.AUTO_START
            self.config.randomOnStartup.value = app_config.settings["app"].get("random_on_startup", True)
            
            # 同步目录设置
            self.config.wallpaperDir.value = app_config.WALLPAPER_DIR
            self.config.cacheDir.value = app_config.CACHE_DIR
            # self.config.toolsDir.value = app_config.TOOLS_DIR
            
            # 同步显示设置
            self.config.notifications.value = app_config.SHOW_NOTIFICATIONS
            self.config.animations.value = app_config.ENABLE_ANIMATIONS
            
            # 同步Real-ESRGAN设置
            self.config.realesrganEnabled.value = app_config.REALESRGAN_ENABLED
            self.config.realesrganPath.value = app_config.REALESRGAN_PATH
            self.config.realesrganScale.value = app_config.REALESRGAN_SCALE
            self.config.realesrganModel.value = app_config.REALESRGAN_MODEL
            
            # 同步托盘设置
            self.config.minimizeOnAutoStart.value = app_config.MINIMIZE_ON_AUTO_START
            self.config.minimizeOnClose.value = app_config.MINIMIZE_ON_CLOSE
            
            # 保存QConfig到文件
            self.config.save()
            
            # 更新界面显示
            self.update_ui_from_config()
            
        except Exception as e:
            print(f"从应用配置同步时出错: {e}")
            import traceback
            traceback.print_exc()

    def create_general_group(self):
        """创建常规设置组"""
        general_group = SettingCardGroup("常规设置", self.scroll_content)
        
        # 主题设置
        self.theme_card = ComboBoxSettingCard(
            configItem=self.config.defaultTheme,
            icon=FIF.BRUSH,
            title="主题",
            content="选择默认主题",
            texts=["浅色", "深色", "跟随系统"],
            parent=general_group
        )
        general_group.addSettingCard(self.theme_card)
        
        # 自动启动
        self.auto_start_card = SwitchSettingCard(
            configItem=self.config.autoStart,
            icon=FIF.POWER_BUTTON,
            title="开机自动启动",
            content="开机时自动启动应用程序",
            parent=general_group
        )
        general_group.addSettingCard(self.auto_start_card)
        
        # 启动时随机选择壁纸
        self.random_startup_card = SwitchSettingCard(
            configItem=self.config.randomOnStartup,
            icon=FIF.CAFE,
            title="启动时随机选择壁纸",
            content="程序启动时自动随机选择一张壁纸",
            parent=general_group
        )
        general_group.addSettingCard(self.random_startup_card)
        
        # 开机自启时最小化到托盘
        self.minimize_startup_card = SwitchSettingCard(
            configItem=self.config.minimizeOnAutoStart,
            icon=FIF.MINIMIZE,
            title="自启时最小化到托盘",
            content="开机自启时自动最小化到系统托盘",
            parent=general_group
        )
        general_group.addSettingCard(self.minimize_startup_card)
        
        # 关闭时最小化到托盘
        self.minimize_close_card = SwitchSettingCard(
            configItem=self.config.minimizeOnClose,
            icon=FIF.CLOSE,
            title="关闭时最小化到托盘",
            content="点击关闭按钮时最小化到系统托盘而不是退出程序",
            parent=general_group
        )
        general_group.addSettingCard(self.minimize_close_card)
        
        self.scroll_layout.addWidget(general_group)

    def create_directory_group(self):
        """创建目录设置组"""
        directory_group = SettingCardGroup("目录设置", self.scroll_content)
        
        # 壁纸目录
        self.wallpaper_dir_card = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "壁纸目录",
            self.config.wallpaperDir.value,  # 使用当前值
            parent=directory_group
        )
        self.wallpaper_dir_card.clicked.connect(self.browse_wallpaper_dir)
        directory_group.addSettingCard(self.wallpaper_dir_card)
        
        # 缓存目录
        self.cache_dir_card = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "缓存目录",
            self.config.cacheDir.value,  # 使用当前值
            parent=directory_group
        )
        self.cache_dir_card.clicked.connect(self.browse_cache_dir)
        directory_group.addSettingCard(self.cache_dir_card)
        
        # # 工具目录
        # self.tools_dir_card = PushSettingCard(
        #     "选择文件夹",
        #     FIF.FOLDER,
        #     "工具目录",
        #     self.config.toolsDir.value,  # 使用当前值
        #     parent=directory_group
        # )
        # self.tools_dir_card.clicked.connect(self.browse_tools_dir)
        # directory_group.addSettingCard(self.tools_dir_card)
        
        self.scroll_layout.addWidget(directory_group)
    
    def create_display_group(self):
        """创建显示设置组"""
        display_group = SettingCardGroup("显示设置", self.scroll_content)
        
        # # 自动随机切换间隔
        # self.interval_card = ComboBoxSettingCard(
        #     FIF.STOP_WATCH,
        #     "自动随机切换间隔",
        #     "壁纸自动随机切换的时间间隔",
        #     texts=["禁用", "5分钟", "10分钟", "30分钟", "1小时", "2小时", "4小时", "8小时"],
        #     parent=display_group
        # )
        # display_group.addSettingCard(self.interval_card)
        
        # 显示通知
        self.notifications_card = SwitchSettingCard(
            configItem=self.config.notifications,
            icon=FIF.CHAT,
            title="显示系统通知",
            content="启用系统通知来显示状态信息",
            parent=display_group
        )
        display_group.addSettingCard(self.notifications_card)
        
        # 启用动画
        self.animations_card = SwitchSettingCard(
            configItem=self.config.animations,
            icon=FIF.PLAY,
            title="启用界面动画",
            content="启用界面切换和交互动画效果",
            parent=display_group
        )
        display_group.addSettingCard(self.animations_card)
        
        self.scroll_layout.addWidget(display_group)
    
    def create_realesrgan_group(self):
        """创建超分辨率设置组"""
        realesrgan_group = SettingCardGroup("超分辨率设置", self.scroll_content)
        
        # 启用超分辨率
        self.realesrgan_enabled_card = SwitchSettingCard(
            configItem=self.config.realesrganEnabled,
            icon=FIF.ZOOM_IN,
            title="启用超分辨率",
            content="使用 Real-ESRGAN 提升图片分辨率",
            parent=realesrgan_group
        )
        realesrgan_group.addSettingCard(self.realesrgan_enabled_card)
        
        # 可执行文件路径
        self.realesrgan_path_card = PushSettingCard(
            text="选择文件",
            icon=FIF.DOCUMENT,
            title="可执行文件路径",
            content="Real-ESRGAN 可执行文件的路径",
            parent=realesrgan_group
        )
        self.realesrgan_path_card.clicked.connect(self.browse_realesrgan_path)
        realesrgan_group.addSettingCard(self.realesrgan_path_card)
        
        # 缩放比例
        self.scale_card = ComboBoxSettingCard(
            configItem=self.config.realesrganScale,
            icon=FIF.ZOOM,
            title="缩放比例",
            content="图片放大的倍数",
            texts=["2x", "3x", "4x"],
            parent=realesrgan_group
        )
        realesrgan_group.addSettingCard(self.scale_card)
        
        # 模型选择
        self.model_card = ComboBoxSettingCard(
            configItem=self.config.realesrganModel,
            icon=FIF.ROBOT,
            title="模型选择",
            content="选择使用的 Real-ESRGAN 模型",
            texts=["realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrgnet-x4plus"],
            parent=realesrgan_group
        )
        realesrgan_group.addSettingCard(self.model_card)
        
        self.scroll_layout.addWidget(realesrgan_group)

    def browse_wallpaper_dir(self):
        """选择壁纸目录"""
        try:
            current_dir = self.config.wallpaperDir.value
            dir_path = QFileDialog.getExistingDirectory(self, "选择壁纸目录", current_dir)
            if dir_path:
                self.wallpaper_dir_card.setContent(dir_path)
                self.config.wallpaperDir.value = dir_path  # 更新配置
                self._notify_settings_changed()  # 通知更改
        except Exception as e:
            self.show_error(f"选择壁纸目录时出错: {str(e)}")
    
    def browse_cache_dir(self):
        """选择缓存目录"""
        try:
            current_dir = self.config.cacheDir.value
            dir_path = QFileDialog.getExistingDirectory(self, "选择缓存目录", current_dir)
            if dir_path:
                self.cache_dir_card.setContent(dir_path)
                self.config.cacheDir.value = dir_path  # 更新配置
                self._notify_settings_changed()  # 通知更改
        except Exception as e:
            self.show_error(f"选择缓存目录时出错: {str(e)}")
    
    # def browse_tools_dir(self):
    #     """选择工具目录"""
    #     try:
    #         current_dir = self.config.toolsDir.value
    #         dir_path = QFileDialog.getExistingDirectory(self, "选择工具目录", current_dir)
    #         if dir_path:
    #             self.tools_dir_card.setContent(dir_path)
    #             self.config.toolsDir.value = dir_path  # 更新配置
    #             self._notify_settings_changed()  # 通知更改
    #     except Exception as e:
    #         self.show_error(f"选择工具目录时出错: {str(e)}")
    
    def browse_realesrgan_path(self):
        """选择Real-ESRGAN可执行文件"""
        try:
            current_path = self.config.realesrganPath.value
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择Real-ESRGAN可执行文件", 
                current_path,
                "可执行文件 (*.exe);;所有文件 (*.*)"
            )
            if file_path:
                self.realesrgan_path_card.setContent(file_path)
                self.config.realesrganPath.value = file_path  # 更新配置
                self._notify_settings_changed()  # 通知更改
        except Exception as e:
            self.show_error(f"选择Real-ESRGAN路径时出错: {str(e)}")
    
    def load_settings_values(self):
        """从配置加载设置值到界面"""
        try:
            config = self.controller.model.manager.config
            
            # 保存原始设置
            self.original_settings = config.settings.copy() if hasattr(config, 'settings') else {}
            
            # 常规设置
            theme_index = 0
            if hasattr(config, 'THEME'):
                if config.THEME == "dark":
                    theme_index = 1
                elif config.THEME == "system":
                    theme_index = 2
            self.theme_card.setValue(theme_index)
            
            lang_index = 0
            if hasattr(config, 'LANGUAGE') and config.LANGUAGE == "en_US":
                lang_index = 1
            # self.language_card.setCurrentIndex(lang_index)
            
            if hasattr(config, 'AUTO_START'):
                self.auto_start_card.setChecked(config.AUTO_START)
            
            # 随机启动设置
            random_startup = config.settings.get("app", {}).get("random_on_startup", True) if hasattr(config, 'settings') else True
            self.random_startup_card.setChecked(random_startup)
            
            # 目录设置
            if hasattr(config, 'WALLPAPER_DIR'):
                self.wallpaper_dir_card.setContent(config.WALLPAPER_DIR)
            if hasattr(config, 'CACHE_DIR'):
                self.cache_dir_card.setContent(config.CACHE_DIR)
            if hasattr(config, 'TOOLS_DIR'):
                self.tools_dir_card.setContent(config.TOOLS_DIR)
            
            # 显示设置
            interval = getattr(config, 'WALLPAPER_CHANGE_INTERVAL', 0)
            interval_index = 0
            if interval == 5: interval_index = 1
            elif interval == 10: interval_index = 2
            elif interval == 30: interval_index = 3
            elif interval == 60: interval_index = 4
            elif interval == 120: interval_index = 5
            elif interval == 240: interval_index = 6
            elif interval == 480: interval_index = 7
            # self.interval_card.setCurrentIndex(interval_index)
            
            if hasattr(config, 'SHOW_NOTIFICATIONS'):
                self.notifications_card.setChecked(config.SHOW_NOTIFICATIONS)
            if hasattr(config, 'ENABLE_ANIMATIONS'):
                self.animations_card.setChecked(config.ENABLE_ANIMATIONS)
            
            # Real-ESRGAN设置
            if hasattr(config, 'REALESRGAN_ENABLED'):
                self.realesrgan_enabled_card.setChecked(config.REALESRGAN_ENABLED)
            if hasattr(config, 'REALESRGAN_PATH'):
                self.realesrgan_path_card.setContent(config.REALESRGAN_PATH)
            
            scale_index = max(0, min(getattr(config, 'REALESRGAN_SCALE', 2) - 2, 2))
            # self.scale_card.setCurrentIndex(scale_index)
            
            model_index = 0
            if hasattr(config, 'REALESRGAN_MODEL'):
                if config.REALESRGAN_MODEL == "realesrgan-x4plus-anime":
                    model_index = 1
                elif config.REALESRGAN_MODEL == "realesrgnet-x4plus":
                    model_index = 2
            # self.model_card.setCurrentIndex(model_index)
            
            # 图库设置
            thumbnail_size = getattr(config, 'THUMBNAIL_SIZE', 200)
            # self.thumbnail_size_card.spinbox.setValue(thumbnail_size)
            
            items_per_row = getattr(config, 'ITEMS_PER_ROW', 0)
            # self.items_per_row_card.spinbox.setValue(items_per_row)
            
            default_sort = getattr(config, 'DEFAULT_SORT', 'filename')
            sort_index = 0
            if default_sort == "date":
                sort_index = 1
            elif default_sort == "size":
                sort_index = 2
            # self.default_sort_card.setCurrentIndex(sort_index)
            
            show_excluded = getattr(config, 'SHOW_EXCLUDED', False)
            # self.show_excluded_card.setChecked(show_excluded)
            
        except Exception as e:
            print(f"加载设置值时出错: {e}")
            self.show_error(f"加载设置失败: {str(e)}")
    
    def save_settings(self):
        """保存设置"""
        try:
            config = self.controller.model.manager.config
            
            # 确保 settings 字典存在
            if not hasattr(config, 'settings') or not config.settings:
                config.settings = {
                    "app": {},
                    "directories": {},
                    "display": {},
                    "realesrgan": {},
                    "gallery": {}
                }
            
            # 常规设置
            theme_values = ["light", "dark", "system"]
            config.settings["app"]["theme"] = theme_values[self.theme_card.configItem]
            
            # lang_values = ["zh_CN", "en_US"]
            # config.settings["app"]["language"] = lang_values[self.language_card.currentIndex()]
            
            config.settings["app"]["auto_start"] = self.auto_start_card.isChecked()
            config.settings["app"]["random_on_startup"] = self.random_startup_card.isChecked()
            config.settings["app"]["minimize_on_auto_start"] = self.minimize_startup_card.isChecked()
            config.settings["app"]["minimize_on_close"] = self.minimize_close_card.isChecked()
            
            # 目录设置
            config.settings["directories"]["wallpaper"] = self.wallpaper_dir_card.contentLabel.text()
            config.settings["directories"]["cache"] = self.cache_dir_card.contentLabel.text()
            config.settings["directories"]["tools"] = self.tools_dir_card.contentLabel.text()
            
            # 显示设置
            interval_values = [0, 5, 10, 30, 60, 120, 240, 480]
            # config.settings["display"]["wallpaper_change_interval"] = interval_values[self.interval_card.currentIndex()]
            config.settings["display"]["show_notifications"] = self.notifications_card.isChecked()
            config.settings["display"]["enable_animations"] = self.animations_card.isChecked()
            
            # Real-ESRGAN设置
            config.settings["realesrgan"]["enabled"] = self.realesrgan_enabled_card.isChecked()
            config.settings["realesrgan"]["executable"] = self.realesrgan_path_card.contentLabel.text()
            # config.settings["realesrgan"]["scale"] = self.scale_card.currentIndex() + 2
            
            model_values = ["realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrgnet-x4plus"]
            # config.settings["realesrgan"]["model"] = model_values[self.model_card.currentIndex()]
            
            # 图库设置
            # config.settings["gallery"]["thumbnail_size"] = self.thumbnail_size_card.spinbox.value()
            # config.settings["gallery"]["items_per_row"] = self.items_per_row_card.spinbox.value()
            
            sort_values = ["filename", "date", "size"]
            # config.settings["gallery"]["default_sort"] = sort_values[self.default_sort_card.currentIndex()]
            # config.settings["gallery"]["show_excluded"] = self.show_excluded_card.isChecked()
            
            # 保存设置到文件
            if config.save_settings():
                # 重新设置属性
                if hasattr(config, '_setup_properties'):
                    config._setup_properties()
                
                # 显示成功消息
                InfoBar.success(
                    title='保存成功',
                    content='设置已成功保存',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self
                )
                
                # 如果设置有变化，发出信号和通知控制器
                if self.original_settings != config.settings:
                    self.settingsChanged.emit()
                    if hasattr(self.controller, 'settings_changed'):
                        self.controller.settings_changed()
                
                return True
            else:
                self.show_error("无法保存设置文件")
                return False
        
        except Exception as e:
            import traceback
            print(f"保存设置时发生错误: {e}")
            print(traceback.format_exc())
            self.show_error(f"保存设置时出错: {str(e)}")
            return False
    
    def cancel_changes(self):
        """取消更改"""
        try:
            # 重新加载设置值，恢复到之前的状态
            self.load_settings_values()
            
            InfoBar.info(
                title='已取消',
                content='设置更改已取消',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
        except Exception as e:
            self.show_error(f"取消更改时出错: {str(e)}")
    
    def restore_defaults(self):
        """恢复默认设置"""
        try:
            config = self.controller.model.manager.config
            
            # 如果配置对象有默认设置，使用它
            if hasattr(config, 'default_settings'):
                config.settings = config.default_settings.copy()
            else:
                # 否则设置一个基本的默认配置
                config.settings = {
                    "app": {
                        "theme": "light",
                        "language": "zh_CN",
                        "auto_start": False,
                        "random_on_startup": True,
                        "minimize_on_auto_start": True,
                        "minimize_on_close": True
                    },
                    "directories": {
                        "wallpaper": "./wallpapers",
                        "cache": "./cache",
                        "tools": "./tools"
                    },
                    "display": {
                        "wallpaper_change_interval": 0,
                        "show_notifications": True,
                        "enable_animations": True
                    },
                    "realesrgan": {
                        "enabled": False,
                        "executable": "",
                        "scale": 2,
                        "model": "realesrgan-x4plus"
                    },
                    "gallery": {
                        "thumbnail_size": 200,
                        "items_per_row": 0,
                        "default_sort": "filename",
                        "show_excluded": False
                    }
                }
            
            # 重新加载界面值
            self.load_settings_values()
            
            InfoBar.success(
                title='恢复完成',
                content='已恢复默认设置',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            self.show_error(f"恢复默认设置时出错: {str(e)}")
    
    def show_error(self, message):
        """显示错误信息"""
        InfoBar.error(
            title='错误',
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )
    
    def showEvent(self, event):
        """在显示设置界面时自动加载配置"""
        super().showEvent(event)
        
        # 初次显示时更新目录卡的显示内容
        if not hasattr(self, '_settings_loaded') or not self._settings_loaded:
            print("设置界面: 首次显示，更新目录卡显示")
            self.wallpaper_dir_card.setContent(self.config.wallpaperDir.value)
            self.cache_dir_card.setContent(self.config.cacheDir.value)
            # self.tools_dir_card.setContent(self.config.toolsDir.value)
            self.realesrgan_path_card.setContent(self.config.realesrganPath.value)
            self._settings_loaded = True
    
    def update_ui_from_config(self):
        """从QConfig更新UI显示"""
        try:
            # 目录设置需要手动更新
            self.wallpaper_dir_card.setContent(self.config.wallpaperDir.value)
            self.cache_dir_card.setContent(self.config.cacheDir.value)
            # self.tools_dir_card.setContent(self.config.toolsDir.value)
            self.realesrgan_path_card.setContent(self.config.realesrganPath.value)
            
            # 其他带有ConfigItem的设置卡会自动更新
            
        except Exception as e:
            print(f"更新UI显示时出错: {e}")