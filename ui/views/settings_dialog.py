from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTabWidget, QWidget, QLabel, QLineEdit, QCheckBox,
                           QSpinBox, QComboBox, QFileDialog, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal

class SettingsDialog(QDialog):
    """设置对话框"""
    
    settingsChanged = pyqtSignal()  # 当设置改变时发出信号
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.original_settings = config.settings.copy()
        self.setup_ui()
        self.load_values()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)
        
        main_layout = QVBoxLayout(self)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个选项卡
        self.create_general_tab()
        self.create_paths_tab()
        self.create_display_tab()
        self.create_realesrgan_tab()
        self.create_gallery_tab()
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)
        
        self.restore_defaults_button = QPushButton("恢复默认")
        self.restore_defaults_button.clicked.connect(self.restore_defaults)
        buttons_layout.addWidget(self.restore_defaults_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("保存")
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_button)
        
        main_layout.addLayout(buttons_layout)
    
    def create_general_tab(self):
        """创建常规选项卡"""
        general_tab = QWidget()
        layout = QFormLayout(general_tab)
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "system"])
        layout.addRow("主题:", self.theme_combo)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        layout.addRow("语言:", self.language_combo)
        
        # 自动启动
        self.auto_start_check = QCheckBox("开机自动启动")
        layout.addRow("", self.auto_start_check)
        
        self.tab_widget.addTab(general_tab, "常规")
    
    def create_paths_tab(self):
        """创建路径选项卡"""
        paths_tab = QWidget()
        layout = QFormLayout(paths_tab)
        
        # 壁纸目录
        wallpaper_layout = QHBoxLayout()
        self.wallpaper_dir_edit = QLineEdit()
        self.wallpaper_dir_edit.setReadOnly(True)
        wallpaper_layout.addWidget(self.wallpaper_dir_edit)
        
        self.browse_wallpaper_button = QPushButton("浏览...")
        self.browse_wallpaper_button.clicked.connect(self.browse_wallpaper_dir)
        wallpaper_layout.addWidget(self.browse_wallpaper_button)
        
        layout.addRow("壁纸目录:", wallpaper_layout)
        
        # 缓存目录
        cache_layout = QHBoxLayout()
        self.cache_dir_edit = QLineEdit()
        self.cache_dir_edit.setReadOnly(True)
        cache_layout.addWidget(self.cache_dir_edit)
        
        self.browse_cache_button = QPushButton("浏览...")
        self.browse_cache_button.clicked.connect(self.browse_cache_dir)
        cache_layout.addWidget(self.browse_cache_button)
        
        layout.addRow("缓存目录:", cache_layout)
        
        # 工具目录
        tools_layout = QHBoxLayout()
        self.tools_dir_edit = QLineEdit()
        self.tools_dir_edit.setReadOnly(True)
        tools_layout.addWidget(self.tools_dir_edit)
        
        self.browse_tools_button = QPushButton("浏览...")
        self.browse_tools_button.clicked.connect(self.browse_tools_dir)
        tools_layout.addWidget(self.browse_tools_button)
        
        layout.addRow("工具目录:", tools_layout)
        
        self.tab_widget.addTab(paths_tab, "路径")
    
    def create_display_tab(self):
        """创建显示选项卡"""
        display_tab = QWidget()
        layout = QFormLayout(display_tab)
        
        # 壁纸自动切换间隔
        self.wallpaper_interval_spin = QSpinBox()
        self.wallpaper_interval_spin.setRange(0, 1440)  # 0-1440分钟 (24小时)
        self.wallpaper_interval_spin.setSuffix(" 分钟")
        self.wallpaper_interval_spin.setSpecialValueText("禁用")
        layout.addRow("自动切换间隔:", self.wallpaper_interval_spin)
        
        # 显示通知
        self.show_notifications_check = QCheckBox("启用系统通知")
        layout.addRow("", self.show_notifications_check)
        
        # 启用动画
        self.enable_animations_check = QCheckBox("启用界面动画")
        layout.addRow("", self.enable_animations_check)
        
        self.tab_widget.addTab(display_tab, "显示")
    
    def create_realesrgan_tab(self):
        """创建Realesrgan选项卡"""
        realesrgan_tab = QWidget()
        layout = QFormLayout(realesrgan_tab)
        
        # 启用Realesrgan
        self.realesrgan_enabled_check = QCheckBox("启用Realesrgan超分辨率")
        layout.addRow("", self.realesrgan_enabled_check)
        
        # Realesrgan可执行文件路径
        realesrgan_layout = QHBoxLayout()
        self.realesrgan_path_edit = QLineEdit()
        realesrgan_layout.addWidget(self.realesrgan_path_edit)
        
        self.browse_realesrgan_button = QPushButton("浏览...")
        self.browse_realesrgan_button.clicked.connect(self.browse_realesrgan_path)
        realesrgan_layout.addWidget(self.browse_realesrgan_button)
        
        layout.addRow("可执行文件:", realesrgan_layout)
        
        # 缩放比例
        self.realesrgan_scale_spin = QSpinBox()
        self.realesrgan_scale_spin.setRange(1, 4)
        layout.addRow("缩放比例:", self.realesrgan_scale_spin)
        
        # 模型选择
        self.realesrgan_model_combo = QComboBox()
        self.realesrgan_model_combo.addItems(["realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrnet-x4plus"])
        layout.addRow("模型:", self.realesrgan_model_combo)
        
        self.tab_widget.addTab(realesrgan_tab, "超分辨率")
    
    def create_gallery_tab(self):
        """创建图库选项卡"""
        gallery_tab = QWidget()
        layout = QFormLayout(gallery_tab)
        
        # 缩略图大小
        self.thumbnail_size_spin = QSpinBox()
        self.thumbnail_size_spin.setRange(100, 300)
        self.thumbnail_size_spin.setSuffix(" 像素")
        layout.addRow("缩略图大小:", self.thumbnail_size_spin)
        
        # 每行显示数量
        self.items_per_row_spin = QSpinBox()
        self.items_per_row_spin.setRange(0, 10)  # 0表示自动
        self.items_per_row_spin.setSpecialValueText("自动")
        layout.addRow("每行显示数量:", self.items_per_row_spin)
        
        # 默认排序
        self.default_sort_combo = QComboBox()
        self.default_sort_combo.addItems(["filename", "date", "size"])
        layout.addRow("默认排序:", self.default_sort_combo)
        
        # 显示已排除的壁纸
        self.show_excluded_check = QCheckBox("默认显示已排除的壁纸")
        layout.addRow("", self.show_excluded_check)
        
        self.tab_widget.addTab(gallery_tab, "图库")
    
    def browse_wallpaper_dir(self):
        """选择壁纸目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择壁纸目录", 
                                                   self.config.WALLPAPER_DIR)
        if dir_path:
            self.wallpaper_dir_edit.setText(dir_path)
    
    def browse_cache_dir(self):
        """选择缓存目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择缓存目录", 
                                                   self.config.CACHE_DIR)
        if dir_path:
            self.cache_dir_edit.setText(dir_path)
    
    def browse_tools_dir(self):
        """选择工具目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择工具目录", 
                                                   self.config.TOOLS_DIR)
        if dir_path:
            self.tools_dir_edit.setText(dir_path)
    
    def browse_realesrgan_path(self):
        """选择Realesrgan可执行文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择Realesrgan可执行文件", 
                                                 self.config.REALESRGAN_PATH,
                                                 "可执行文件 (*.exe);;所有文件 (*.*)")
        if file_path:
            self.realesrgan_path_edit.setText(file_path)
    
    def load_values(self):
        """从配置加载当前值"""
        # 常规选项
        self.theme_combo.setCurrentText(self.config.THEME)
        self.language_combo.setCurrentText(self.config.LANGUAGE)
        self.auto_start_check.setChecked(self.config.AUTO_START)
        
        # 路径选项
        self.wallpaper_dir_edit.setText(self.config.WALLPAPER_DIR)
        self.cache_dir_edit.setText(self.config.CACHE_DIR)
        self.tools_dir_edit.setText(self.config.TOOLS_DIR)
        
        # 显示选项
        self.wallpaper_interval_spin.setValue(self.config.WALLPAPER_CHANGE_INTERVAL)
        self.show_notifications_check.setChecked(self.config.SHOW_NOTIFICATIONS)
        self.enable_animations_check.setChecked(self.config.ENABLE_ANIMATIONS)
        
        # Realesrgan选项
        self.realesrgan_enabled_check.setChecked(self.config.REALESRGAN_ENABLED)
        self.realesrgan_path_edit.setText(self.config.REALESRGAN_PATH)
        self.realesrgan_scale_spin.setValue(self.config.REALESRGAN_SCALE)
        self.realesrgan_model_combo.setCurrentText(self.config.REALESRGAN_MODEL)
        
        # 图库选项
        self.thumbnail_size_spin.setValue(self.config.THUMBNAIL_SIZE)
        self.items_per_row_spin.setValue(self.config.ITEMS_PER_ROW)
        self.default_sort_combo.setCurrentText(self.config.DEFAULT_SORT)
        self.show_excluded_check.setChecked(self.config.SHOW_EXCLUDED)
    
    def save_settings(self):
        """保存设置"""
        # 常规选项
        self.config.settings["app"]["theme"] = self.theme_combo.currentText()
        self.config.settings["app"]["language"] = self.language_combo.currentText()
        self.config.settings["app"]["auto_start"] = self.auto_start_check.isChecked()
        
        # 路径选项
        self.config.settings["directories"]["wallpaper"] = self.wallpaper_dir_edit.text()
        self.config.settings["directories"]["cache"] = self.cache_dir_edit.text()
        self.config.settings["directories"]["tools"] = self.tools_dir_edit.text()
        
        # 显示选项
        self.config.settings["display"]["wallpaper_change_interval"] = self.wallpaper_interval_spin.value()
        self.config.settings["display"]["show_notifications"] = self.show_notifications_check.isChecked()
        self.config.settings["display"]["enable_animations"] = self.enable_animations_check.isChecked()
        
        # Realesrgan选项
        self.config.settings["realesrgan"]["enabled"] = self.realesrgan_enabled_check.isChecked()
        self.config.settings["realesrgan"]["executable"] = self.realesrgan_path_edit.text()
        self.config.settings["realesrgan"]["scale"] = self.realesrgan_scale_spin.value()
        self.config.settings["realesrgan"]["model"] = self.realesrgan_model_combo.currentText()
        
        # 图库选项
        self.config.settings["gallery"]["thumbnail_size"] = self.thumbnail_size_spin.value()
        self.config.settings["gallery"]["items_per_row"] = self.items_per_row_spin.value()
        self.config.settings["gallery"]["default_sort"] = self.default_sort_combo.currentText()
        self.config.settings["gallery"]["show_excluded"] = self.show_excluded_check.isChecked()
        
        # 保存设置到文件并更新配置对象
        if self.config.save_settings():
            # 重新设置属性
            self.config._setup_properties()
            
            # 如果设置有变化，发出信号
            if self.original_settings != self.config.settings:
                self.settingsChanged.emit()
                
            self.accept()
        
    def restore_defaults(self):
        """恢复默认设置"""
        self.config.settings = self.config.default_settings.copy()
        self.load_values()