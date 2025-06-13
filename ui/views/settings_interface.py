from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
                            QPushButton, QScrollArea, QComboBox, QLineEdit, QCheckBox,
                            QToolButton, QGridLayout, QSpinBox, QFileDialog, QGroupBox, QFormLayout,
                            QTabWidget)

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentWindow, FluentIcon as FIF, NavigationItemPosition,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, SubtitleLabel, CaptionLabel, 
                          setTheme, Theme, InfoBar, InfoBarPosition, CardWidget, 
                          ScrollArea, ExpandLayout, SettingCardGroup, SwitchSettingCard,
                          ComboBoxSettingCard, PushSettingCard, LineEdit)

class SettingsInterface(QFrame):
    """设置界面 - 整合了原SettingsDialog功能"""
    
    # 定义信号
    settingsChanged = pyqtSignal()  # 当设置改变时发出信号
    
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller
        self.setObjectName("Settings-Interface")
        
        # 保存原始设置用于比较
        self.original_settings = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置设置界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加标题
        title_label = SubtitleLabel("设置")
        main_layout.addWidget(title_label)
        
        # 创建滚动区域
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建滚动内容
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)
        
        # 创建各个设置组
        self.create_general_group()
        self.create_directory_group()
        self.create_display_group()
        self.create_realesrgan_group()
        # self.create_gallery_group()
        
        # 添加弹性空间
        self.scroll_layout.addStretch(1)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, 1)
        
        # 底部按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        
        # 恢复默认按钮
        self.restore_button = TransparentToolButton("恢复默认")
        self.restore_button.setIcon(FIF.RETURN)
        self.restore_button.clicked.connect(self.restore_defaults)
        buttons_layout.addWidget(self.restore_button)
        
        buttons_layout.addStretch(1)
        
        # 取消和保存按钮
        self.cancel_button = TransparentToolButton("取消")
        self.cancel_button.setIcon(FIF.CANCEL)
        self.cancel_button.clicked.connect(self.cancel_changes)
        buttons_layout.addWidget(self.cancel_button)
        
        self.save_button = PrimaryPushButton("保存设置")
        self.save_button.setIcon(FIF.SAVE)
        self.save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_button)
        
        main_layout.addLayout(buttons_layout)
    
    def create_general_group(self):
        """创建常规设置组"""
        general_group = SettingCardGroup("常规设置", self.scroll_content)
        
        # # 主题设置
        # self.theme_card = ComboBoxSettingCard(
        #     FIF.BRUSH,
        #     "主题",
        #     "选择应用程序主题",
        #     texts=["浅色", "深色", "跟随系统"],
        #     parent=general_group
        # )
        # general_group.addSettingCard(self.theme_card)
        
        # 自动启动
        self.auto_start_card = SwitchSettingCard(
            FIF.POWER_BUTTON,
            "开机自动启动",
            "开机时自动启动应用程序",
            parent=general_group
        )
        general_group.addSettingCard(self.auto_start_card)
        
        # 启动时随机选择壁纸
        self.random_startup_card = SwitchSettingCard(
            FIF.CAFE,
            "启动时随机选择壁纸",
            "程序启动时自动随机选择一张壁纸",
            parent=general_group
        )
        general_group.addSettingCard(self.random_startup_card)
        
        self.scroll_layout.addWidget(general_group)
    
    def create_directory_group(self):
        """创建目录设置组"""
        directory_group = SettingCardGroup("目录设置", self.scroll_content)
        
        # 壁纸目录
        self.wallpaper_dir_card = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "壁纸目录",
            "存放壁纸文件的目录",
            parent=directory_group
        )
        self.wallpaper_dir_card.clicked.connect(self.browse_wallpaper_dir)
        directory_group.addSettingCard(self.wallpaper_dir_card)
        
        # 缓存目录
        self.cache_dir_card = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "缓存目录",
            "存放临时文件和缓存的目录",
            parent=directory_group
        )
        self.cache_dir_card.clicked.connect(self.browse_cache_dir)
        directory_group.addSettingCard(self.cache_dir_card)
        
        # 工具目录
        self.tools_dir_card = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "工具目录",
            "存放外部工具的目录",
            parent=directory_group
        )
        self.tools_dir_card.clicked.connect(self.browse_tools_dir)
        directory_group.addSettingCard(self.tools_dir_card)
        
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
            FIF.CHAT,
            "显示系统通知",
            "启用系统通知来显示状态信息",
            parent=display_group
        )
        display_group.addSettingCard(self.notifications_card)
        
        # 启用动画
        self.animations_card = SwitchSettingCard(
            FIF.PLAY,
            "启用界面动画",
            "启用界面切换和交互动画效果",
            parent=display_group
        )
        display_group.addSettingCard(self.animations_card)
        
        self.scroll_layout.addWidget(display_group)
    
    def create_realesrgan_group(self):
        """创建超分辨率设置组"""
        realesrgan_group = SettingCardGroup("超分辨率设置", self.scroll_content)
        
        # 启用超分辨率
        self.realesrgan_enabled_card = SwitchSettingCard(
            FIF.ZOOM_IN,
            "启用超分辨率",
            "使用 Real-ESRGAN 提升图片分辨率",
            parent=realesrgan_group
        )
        realesrgan_group.addSettingCard(self.realesrgan_enabled_card)
        
        # 可执行文件路径
        self.realesrgan_path_card = PushSettingCard(
            "选择文件",
            FIF.DOCUMENT,
            "可执行文件路径",
            "Real-ESRGAN 可执行文件的路径",
            parent=realesrgan_group
        )
        self.realesrgan_path_card.clicked.connect(self.browse_realesrgan_path)
        realesrgan_group.addSettingCard(self.realesrgan_path_card)
        
        # # 缩放比例
        # self.scale_card = ComboBoxSettingCard(
        #     FIF.ZOOM,
        #     "缩放比例",
        #     "图片放大的倍数",
        #     texts=["2x", "3x", "4x"],
        #     parent=realesrgan_group
        # )
        # realesrgan_group.addSettingCard(self.scale_card)
        
        # 模型选择
        # self.model_card = ComboBoxSettingCard(
        #     FIF.ROBOT,
        #     "模型选择",
        #     "选择使用的 Real-ESRGAN 模型",
        #     texts=["realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrnet-x4plus"],
        #     parent=realesrgan_group
        # )
        # realesrgan_group.addSettingCard(self.model_card)
        
        self.scroll_layout.addWidget(realesrgan_group)

    def browse_wallpaper_dir(self):
        """选择壁纸目录"""
        try:
            current_dir = getattr(self.controller.model.manager.config, 'WALLPAPER_DIR', '')
            dir_path = QFileDialog.getExistingDirectory(self, "选择壁纸目录", current_dir)
            if dir_path:
                self.wallpaper_dir_card.setContent(dir_path)
        except Exception as e:
            self.show_error(f"选择壁纸目录时出错: {str(e)}")
    
    def browse_cache_dir(self):
        """选择缓存目录"""
        try:
            current_dir = getattr(self.controller.model.manager.config, 'CACHE_DIR', '')
            dir_path = QFileDialog.getExistingDirectory(self, "选择缓存目录", current_dir)
            if dir_path:
                self.cache_dir_card.setContent(dir_path)
        except Exception as e:
            self.show_error(f"选择缓存目录时出错: {str(e)}")
    
    def browse_tools_dir(self):
        """选择工具目录"""
        try:
            current_dir = getattr(self.controller.model.manager.config, 'TOOLS_DIR', '')
            dir_path = QFileDialog.getExistingDirectory(self, "选择工具目录", current_dir)
            if dir_path:
                self.tools_dir_card.setContent(dir_path)
        except Exception as e:
            self.show_error(f"选择工具目录时出错: {str(e)}")
    
    def browse_realesrgan_path(self):
        """选择Real-ESRGAN可执行文件"""
        try:
            current_path = getattr(self.controller.model.manager.config, 'REALESRGAN_PATH', '')
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择Real-ESRGAN可执行文件", 
                current_path,
                "可执行文件 (*.exe);;所有文件 (*.*)"
            )
            if file_path:
                self.realesrgan_path_card.setContent(file_path)
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
            self.theme_card.setCurrentIndex(theme_index)
            
            lang_index = 0
            if hasattr(config, 'LANGUAGE') and config.LANGUAGE == "en_US":
                lang_index = 1
            self.language_card.setCurrentIndex(lang_index)
            
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
            self.interval_card.setCurrentIndex(interval_index)
            
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
            self.scale_card.setCurrentIndex(scale_index)
            
            model_index = 0
            if hasattr(config, 'REALESRGAN_MODEL'):
                if config.REALESRGAN_MODEL == "realesrgan-x4plus-anime":
                    model_index = 1
                elif config.REALESRGAN_MODEL == "realesrnet-x4plus":
                    model_index = 2
            self.model_card.setCurrentIndex(model_index)
            
            # 图库设置
            thumbnail_size = getattr(config, 'THUMBNAIL_SIZE', 200)
            self.thumbnail_size_card.spinbox.setValue(thumbnail_size)
            
            items_per_row = getattr(config, 'ITEMS_PER_ROW', 0)
            self.items_per_row_card.spinbox.setValue(items_per_row)
            
            default_sort = getattr(config, 'DEFAULT_SORT', 'filename')
            sort_index = 0
            if default_sort == "date":
                sort_index = 1
            elif default_sort == "size":
                sort_index = 2
            self.default_sort_card.setCurrentIndex(sort_index)
            
            show_excluded = getattr(config, 'SHOW_EXCLUDED', False)
            self.show_excluded_card.setChecked(show_excluded)
            
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
            config.settings["app"]["theme"] = theme_values[self.theme_card.currentIndex()]
            
            lang_values = ["zh_CN", "en_US"]
            config.settings["app"]["language"] = lang_values[self.language_card.currentIndex()]
            
            config.settings["app"]["auto_start"] = self.auto_start_card.isChecked()
            config.settings["app"]["random_on_startup"] = self.random_startup_card.isChecked()
            
            # 目录设置
            config.settings["directories"]["wallpaper"] = self.wallpaper_dir_card.contentLabel.text()
            config.settings["directories"]["cache"] = self.cache_dir_card.contentLabel.text()
            config.settings["directories"]["tools"] = self.tools_dir_card.contentLabel.text()
            
            # 显示设置
            interval_values = [0, 5, 10, 30, 60, 120, 240, 480]
            config.settings["display"]["wallpaper_change_interval"] = interval_values[self.interval_card.currentIndex()]
            config.settings["display"]["show_notifications"] = self.notifications_card.isChecked()
            config.settings["display"]["enable_animations"] = self.animations_card.isChecked()
            
            # Real-ESRGAN设置
            config.settings["realesrgan"]["enabled"] = self.realesrgan_enabled_card.isChecked()
            config.settings["realesrgan"]["executable"] = self.realesrgan_path_card.contentLabel.text()
            config.settings["realesrgan"]["scale"] = self.scale_card.currentIndex() + 2
            
            model_values = ["realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrnet-x4plus"]
            config.settings["realesrgan"]["model"] = model_values[self.model_card.currentIndex()]
            
            # 图库设置
            config.settings["gallery"]["thumbnail_size"] = self.thumbnail_size_card.spinbox.value()
            config.settings["gallery"]["items_per_row"] = self.items_per_row_card.spinbox.value()
            
            sort_values = ["filename", "date", "size"]
            config.settings["gallery"]["default_sort"] = sort_values[self.default_sort_card.currentIndex()]
            config.settings["gallery"]["show_excluded"] = self.show_excluded_card.isChecked()
            
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
                        "random_on_startup": True
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