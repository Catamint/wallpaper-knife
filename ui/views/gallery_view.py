import base64
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                            QPushButton, QScrollArea, QComboBox, QLineEdit, QCheckBox,
                            QToolButton, QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QPixmap, QIcon, QPalette, QColor

class ThumbnailWidget(QFrame):
    """单个缩略图小部件"""
    clicked = pyqtSignal(str)  # 发送文件名信号
    excludeClicked = pyqtSignal(str)  # 排除按钮信号
    includeClicked = pyqtSignal(str)  # 恢复按钮信号
    
    def __init__(self, filename, info, is_excluded=False, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.info = info
        self.is_excluded = is_excluded
        
        # 设置基本属性
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setFixedSize(200, 180)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # 缩略图显示区域
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setMinimumSize(180, 120)
        self.thumbnail_label.setScaledContents(False)
        layout.addWidget(self.thumbnail_label)
        
        # 文件名标签
        display_name = info.get("display_name", filename[:20])
        if len(display_name) > 20:
            display_name = display_name[:17] + "..."
            
        self.name_label = QLabel(display_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setToolTip(filename)
        layout.addWidget(self.name_label)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        # 按钮: 排除/恢复
        if is_excluded:
            self.toggle_button = QToolButton()
            self.toggle_button.setText("恢复")
            self.toggle_button.setToolTip("将此壁纸从排除列表移除")
            self.toggle_button.clicked.connect(self._on_include_clicked)
            
            # 设置灰色边框表示已排除
            self.setStyleSheet("ThumbnailWidget { background-color: rgba(100, 100, 100, 30); }")
        else:
            self.toggle_button = QToolButton()
            self.toggle_button.setText("排除")
            self.toggle_button.setToolTip("将此壁纸加入排除列表")
            self.toggle_button.clicked.connect(self._on_exclude_clicked)
        
        buttons_layout.addWidget(self.toggle_button)
        layout.addLayout(buttons_layout)
        
        # 加载缩略图
        self._load_thumbnail()
    
    def _load_thumbnail(self):
        """加载缩略图"""
        try:
            if "view_pic" in self.info and self.info["view_pic"]:
                # 从base64加载
                base64_data = self.info["view_pic"]
                pixmap = QPixmap()
                pixmap.loadFromData(QByteArray.fromBase64(base64_data.encode()))
            else:
                # 从文件加载
                pixmap = QPixmap(self.info["path"])
                # 调整大小以适应标签
                pixmap = pixmap.scaled(180, 120, Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
                
                # 如果需要，创建并保存缩略图的base64
                if "view_pic" not in self.info:
                    buffer = QBuffer()
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    pixmap.save(buffer, "JPG", 80)
                    base64_data = base64.b64encode(buffer.data()).decode()
                    self.info["view_pic"] = base64_data
            
            # 设置缩略图
            self.thumbnail_label.setPixmap(pixmap)
            
        except Exception as e:
            # 加载失败时显示占位图
            self.thumbnail_label.setText(f"加载失败\n{str(e)}")
    
    def _on_exclude_clicked(self):
        """排除按钮点击事件"""
        self.excludeClicked.emit(self.filename)
    
    def _on_include_clicked(self):
        """恢复按钮点击事件"""
        self.includeClicked.emit(self.filename)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 只在缩略图区域点击时触发
            if self.thumbnail_label.geometry().contains(event.pos()):
                self.clicked.emit(self.filename)
        super().mousePressEvent(event)


class GalleryView(QWidget):
    """壁纸图库预览视图"""
    wallpaperSelected = pyqtSignal(str)  # 发送选中的壁纸文件名
    excludeWallpaper = pyqtSignal(str)   # 排除壁纸
    includeWallpaper = pyqtSignal(str)   # 恢复壁纸
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wallpaper_data = {}  # 存储所有壁纸数据
        self.excluded_files = set()  # 排除的壁纸
        self.current_filter = "all"  # 当前筛选: all, included, excluded
        self.search_text = ""  # 搜索文本
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        
        # 顶部控制区域
        controls_layout = QHBoxLayout()
        
        # 筛选下拉框
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("所有壁纸", "all")
        self.filter_combo.addItem("已启用", "included")
        self.filter_combo.addItem("已排除", "excluded")
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        controls_layout.addWidget(QLabel("筛选:"))
        controls_layout.addWidget(self.filter_combo)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索壁纸...")
        self.search_input.textChanged.connect(self.on_search_changed)
        controls_layout.addWidget(self.search_input)
        
        # 批量操作按钮
        self.batch_exclude_button = QPushButton("排除选中")
        self.batch_exclude_button.clicked.connect(self.on_batch_exclude)
        controls_layout.addWidget(self.batch_exclude_button)
        
        self.batch_include_button = QPushButton("恢复选中")
        self.batch_include_button.clicked.connect(self.on_batch_include)
        controls_layout.addWidget(self.batch_include_button)
        
        main_layout.addLayout(controls_layout)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建网格布局容器
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # 底部状态
        self.status_label = QLabel("准备就绪")
        main_layout.addWidget(self.status_label)
    
    def set_data(self, wallpaper_data):
        """设置壁纸数据"""
        self.wallpaper_data = wallpaper_data
        self.refresh()
    
    def refresh(self):
        """刷新显示"""
        # 清空现有内容
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 过滤和排序数据
        filtered_data = {}
        for filename, info in self.wallpaper_data.items():
            is_excluded = info.get("excluded", False)
            
            # 应用筛选
            if self.current_filter == "included" and is_excluded:
                continue
            elif self.current_filter == "excluded" and not is_excluded:
                continue
                
            # 应用搜索
            if self.search_text:
                display_name = info.get("display_name", filename)
                if self.search_text.lower() not in display_name.lower() and \
                   self.search_text.lower() not in filename.lower():
                    continue
            
            filtered_data[filename] = info
        
        # 排序 (按文件名)
        sorted_items = sorted(filtered_data.items(), key=lambda x: x[0])
        
        # 填充网格
        row, col = 0, 0
        max_cols = max(1, self.width() // 220)  # 每行最多显示的缩略图数
        
        for filename, info in sorted_items:
            is_excluded = info.get("excluded", False)
            thumbnail = ThumbnailWidget(filename, info, is_excluded)
            
            # 连接信号
            thumbnail.clicked.connect(self.wallpaperSelected)
            thumbnail.excludeClicked.connect(self.on_exclude_wallpaper)
            thumbnail.includeClicked.connect(self.on_include_wallpaper)
            
            # 添加到网格
            self.grid_layout.addWidget(thumbnail, row, col)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 更新状态
        self.status_label.setText(f"显示 {len(filtered_data)} 张壁纸 (共 {len(self.wallpaper_data)} 张)")
    
    def resizeEvent(self, event):
        """窗口大小改变时重新布局"""
        super().resizeEvent(event)
        self.refresh()
    
    def on_filter_changed(self):
        """筛选条件改变"""
        self.current_filter = self.filter_combo.currentData()
        self.refresh()
    
    def on_search_changed(self, text):
        """搜索文本改变"""
        self.search_text = text
        self.refresh()
    
    def on_exclude_wallpaper(self, filename):
        """将壁纸添加到排除列表"""
        self.excluded_files.add(filename)
        self.excludeWallpaper.emit(filename)
        self.refresh()
    
    def on_include_wallpaper(self, filename):
        """将壁纸从排除列表移除"""
        if filename in self.excluded_files:
            self.excluded_files.remove(filename)
            self.includeWallpaper.emit(filename)
            self.refresh()
    
    def on_batch_exclude(self):
        """批量排除选中的壁纸"""
        # 这里需要实现批量选择功能
        # 暂未实现，留作扩展功能
        pass
    
    def on_batch_include(self):
        """批量恢复选中的壁纸"""
        # 这里需要实现批量选择功能
        # 暂未实现，留作扩展功能
        pass