from PyQt6.QtCore import Qt, pyqtSlot, QSize
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
                          BoolValidator, FolderValidator, pyqtSignal)
import os

from .. import wallpaperCfg

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
        # self.sync_from_app_config()
    
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
        self.config.defaultTheme.valueChanged.connect(self._on_defaultTheme_changed)
        
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
    
    def _on_defaultTheme_changed(self, defaultTheme):
        """主题改变时的处理"""
        # 应用主题
        setTheme(defaultTheme)
        self.config.set(self.config.defaultTheme, defaultTheme)
        self._notify_settings_changed()
    
    def _on_auto_start_changed(self, enabled):
        """自启动设置改变时的处理"""
        if hasattr(self.controller, 'set_auto_start'):
            self.controller.set_auto_start(enabled)
        self._notify_settings_changed()
    
    def _on_wallpaper_dir_changed(self, folder):
        """壁纸目录改变时的处理"""
        self.config.set(self.config.wallpaperDir, folder)
        self._notify_settings_changed()
    
    def _on_cache_dir_changed(self, folder):
        """缓存目录改变时的处理"""
        self.config.set(self.config.cacheDir, folder)
        self._notify_settings_changed()
    
    def _on_tools_dir_changed(self, folder):
        """工具目录改变时的处理"""
        self.config.set(self.config.toolsDir, folder)
        self._notify_settings_changed()
    
    def _on_realesrgan_path_changed(self, path):
        """Real-ESRGAN路径改变时的处理"""
        self.config.set(self.config.realesrganPath, path)
        self._notify_settings_changed()
    
    def _notify_settings_changed(self):
        """通知设置已改变"""
        try:
            # 保存设置到配置文件
            print("保存设置到配置文件")
            # print(f"当前配置: {self.config}")
            self.config.save()  # 保存配置
            print("设置已保存")
            # 发出设置已更改信号
            # self.settingsChanged.emit()
            
        except Exception as e:
            import traceback
            print(f"保存设置时发生错误: {e}")
            print(traceback.format_exc())
            self.show_error(f"保存设置时出错: {str(e)}")

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
        
        # 工具目录
        self.tools_dir_card = PushSettingCard(
            "选择文件夹",
            FIF.FOLDER,
            "工具目录",
            self.config.toolsDir.value,  # 使用当前值
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
    
    def browse_tools_dir(self):
        """选择工具目录"""
        try:
            current_dir = self.config.toolsDir.value
            dir_path = QFileDialog.getExistingDirectory(self, "选择工具目录", current_dir)
            if dir_path:
                self.tools_dir_card.setContent(dir_path)
                self.config.toolsDir.value = dir_path  # 更新配置
                self._notify_settings_changed()  # 通知更改
        except Exception as e:
            self.show_error(f"选择工具目录时出错: {str(e)}")
    
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
