import base64
from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal, QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
                            QPushButton, QScrollArea, QComboBox, QLineEdit, QCheckBox,
                            QToolButton, QGridLayout)

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentWindow, FluentIcon as FIF, NavigationItemPosition,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, SubtitleLabel, CaptionLabel, 
                          setTheme, Theme, InfoBar, InfoBarPosition)


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
            self.toggle_button = TransparentToolButton(FIF.ACCEPT)
            self.toggle_button.setText("恢复")
            self.toggle_button.setToolTip("将此壁纸从排除列表移除")
            self.toggle_button.clicked.connect(self._on_include_clicked)
            
            # 设置灰色边框表示已排除
            self.setStyleSheet("ThumbnailWidget { background-color: rgba(100, 100, 100, 30); }")
        else:
            self.toggle_button = TransparentToolButton(FIF.CANCEL)
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


class GalleryInterface(QFrame):
    """图库界面 - 整合了原GalleryView功能"""
    
    # 定义信号
    wallpaperSelected = pyqtSignal(str)  # 发送选中的壁纸文件名
    excludeWallpaper = pyqtSignal(str)   # 排除壁纸
    includeWallpaper = pyqtSignal(str)   # 恢复壁纸
    
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller
        self.setObjectName("Gallery-Interface")
        
        # 数据存储
        self.wallpaper_data = {}  # 存储所有壁纸数据
        self.excluded_files = set()  # 排除的壁纸
        self.current_filter = "all"  # 当前筛选: all, included, excluded
        self.search_text = ""  # 搜索文本
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置图库界面"""
        main_layout = QVBoxLayout(self)
        
        # 顶部标题和控制区域
        header_layout = QVBoxLayout()
        
        # 标题
        title_label = SubtitleLabel("壁纸图库")
        header_layout.addWidget(title_label)
        
        # 控制区域
        controls_layout = QHBoxLayout()
        
        # 筛选下拉框
        filter_label = QLabel("筛选:")
        self.filter_combo = ComboBox()
        self.filter_combo.addItem("所有壁纸")
        self.filter_combo.addItem("已启用")
        self.filter_combo.addItem("已排除")
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        
        # 搜索框
        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索壁纸...")
        self.search_input.textChanged.connect(self.on_search_changed)
        
        # 批量操作按钮
        self.batch_exclude_button = PrimaryPushButton("排除选中")
        self.batch_exclude_button.setIcon(FIF.CANCEL)
        self.batch_exclude_button.clicked.connect(self.on_batch_exclude)
        
        self.batch_include_button = PrimaryPushButton("恢复选中")
        self.batch_include_button.setIcon(FIF.ACCEPT)
        self.batch_include_button.clicked.connect(self.on_batch_include)
        
        # 刷新按钮
        self.refresh_button = ToolButton(FIF.SYNC)
        self.refresh_button.setToolTip("刷新图库")
        self.refresh_button.clicked.connect(self.refresh_gallery)
        
        # 添加控件到布局
        controls_layout.addWidget(filter_label)
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.search_input, 1)  # 搜索框占用更多空间
        controls_layout.addWidget(self.batch_exclude_button)
        controls_layout.addWidget(self.batch_include_button)
        controls_layout.addWidget(self.refresh_button)
        
        header_layout.addLayout(controls_layout)
        main_layout.addLayout(header_layout)
        
        # 创建滚动区域用于显示缩略图
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
        
        # 底部状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.status_label)
    
    def connect_signals(self):
        """连接信号到控制器"""
        try:
            # 连接壁纸选择信号
            if hasattr(self.controller, 'select_wallpaper_from_gallery'):
                self.wallpaperSelected.connect(self.controller.select_wallpaper_from_gallery)
            
            # 连接排除壁纸信号
            if hasattr(self.controller, 'exclude_wallpaper'):
                self.excludeWallpaper.connect(self.controller.exclude_wallpaper)
            
            # 连接恢复壁纸信号
            if hasattr(self.controller, 'include_wallpaper'):
                self.includeWallpaper.connect(self.controller.include_wallpaper)
                
        except Exception as e:
            print(f"连接信号时出错: {e}")
    
    def set_data(self, wallpaper_data):
        """设置壁纸数据"""
        try:
            self.wallpaper_data = wallpaper_data or {}
            self.refresh_display()
        except Exception as e:
            print(f"设置壁纸数据时出错: {e}")
            self.show_error(f"设置数据失败: {str(e)}")
    
    def refresh_display(self):
        """刷新显示"""
        try:
            # 清空现有内容
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 过滤和排序数据
            filtered_data = self._filter_wallpaper_data()
            
            # 如果没有数据，显示提示
            if not filtered_data:
                self._show_empty_message()
                return
            
            # 排序 (按文件名)
            sorted_items = sorted(filtered_data.items(), key=lambda x: x[0])
            
            # 填充网格
            self._populate_grid(sorted_items)
            
            # 更新状态
            self.status_label.setText(f"显示 {len(filtered_data)} 张壁纸 (共 {len(self.wallpaper_data)} 张)")
            
        except Exception as e:
            print(f"刷新显示时出错: {e}")
            self.show_error(f"刷新显示失败: {str(e)}")
    
    def _filter_wallpaper_data(self):
        """过滤壁纸数据"""
        filtered_data = {}
        
        for filename, info in self.wallpaper_data.items():
            is_excluded = info.get("excluded", False)
            
            # 应用筛选
            filter_index = self.filter_combo.currentIndex()
            if filter_index == 1 and is_excluded:  # 只显示已启用
                continue
            elif filter_index == 2 and not is_excluded:  # 只显示已排除
                continue
                
            # 应用搜索
            if self.search_text:
                display_name = info.get("display_name", filename)
                if (self.search_text.lower() not in display_name.lower() and 
                    self.search_text.lower() not in filename.lower()):
                    continue
            
            filtered_data[filename] = info
        
        return filtered_data
    
    def _show_empty_message(self):
        """显示空消息"""
        empty_label = QLabel()
        if self.search_text:
            empty_label.setText(f"没有找到包含 '{self.search_text}' 的壁纸")
        elif self.filter_combo.currentIndex() == 1:
            empty_label.setText("没有已启用的壁纸")
        elif self.filter_combo.currentIndex() == 2:
            empty_label.setText("没有已排除的壁纸")
        else:
            empty_label.setText("没有壁纸数据\n请确保壁纸目录中有图片文件")
        
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("color: gray; font-size: 14pt; padding: 50px;")
        self.grid_layout.addWidget(empty_label, 0, 0)
        
        self.status_label.setText("没有壁纸显示")
    
    def _populate_grid(self, sorted_items):
        """填充网格布局"""
        row, col = 0, 0
        max_cols = max(1, self.width() // 220)  # 每行最多显示的缩略图数
        
        for filename, info in sorted_items:
            is_excluded = info.get("excluded", False)
            thumbnail = ThumbnailWidget(filename, info, is_excluded)
            
            # 连接缩略图信号
            thumbnail.clicked.connect(self._on_thumbnail_clicked)
            thumbnail.excludeClicked.connect(self._on_exclude_wallpaper)
            thumbnail.includeClicked.connect(self._on_include_wallpaper)
            
            # 添加到网格
            self.grid_layout.addWidget(thumbnail, row, col)
            
            # 更新行列位置
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def resizeEvent(self, event):
        """窗口大小改变时重新布局"""
        super().resizeEvent(event)
        # 延迟刷新以避免频繁重绘
        if hasattr(self, 'wallpaper_data') and self.wallpaper_data:
            self.refresh_display()
    
    def on_filter_changed(self):
        """筛选条件改变"""
        filter_names = ["all", "included", "excluded"]
        self.current_filter = filter_names[self.filter_combo.currentIndex()]
        self.refresh_display()
    
    def on_search_changed(self, text):
        """搜索文本改变"""
        self.search_text = text.strip()
        self.refresh_display()
    
    def _on_thumbnail_clicked(self, filename):
        """缩略图点击事件"""
        try:
            self.wallpaperSelected.emit(filename)
        except Exception as e:
            print(f"缩略图点击处理出错: {e}")
    
    def _on_exclude_wallpaper(self, filename):
        """将壁纸添加到排除列表"""
        try:
            self.excluded_files.add(filename)
            # 更新数据中的排除状态
            if filename in self.wallpaper_data:
                self.wallpaper_data[filename]["excluded"] = True
            
            self.excludeWallpaper.emit(filename)
            self.refresh_display()
            
            # 显示成功消息
            InfoBar.success(
                title='操作成功',
                content=f'已排除壁纸: {filename}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
            
        except Exception as e:
            print(f"排除壁纸时出错: {e}")
            self.show_error(f"排除壁纸失败: {str(e)}")
    
    def _on_include_wallpaper(self, filename):
        """将壁纸从排除列表移除"""
        try:
            if filename in self.excluded_files:
                self.excluded_files.remove(filename)
            
            # 更新数据中的排除状态
            if filename in self.wallpaper_data:
                self.wallpaper_data[filename]["excluded"] = False
            
            self.includeWallpaper.emit(filename)
            self.refresh_display()
            
            # 显示成功消息
            InfoBar.success(
                title='操作成功',
                content=f'已恢复壁纸: {filename}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self
            )
            
        except Exception as e:
            print(f"恢复壁纸时出错: {e}")
            self.show_error(f"恢复壁纸失败: {str(e)}")
    
    def refresh_gallery(self):
        """刷新图库"""
        try:
            if hasattr(self.controller, 'refresh_gallery'):
                self.controller.refresh_gallery()
            else:
                # 如果控制器没有刷新方法，直接刷新显示
                self.refresh_display()
                
            InfoBar.success(
                title='刷新完成',
                content='图库已刷新',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=self
            )
            
        except Exception as e:
            print(f"刷新图库时出错: {e}")
            self.show_error(f"刷新图库失败: {str(e)}")
    
    def on_batch_exclude(self):
        """批量排除选中的壁纸"""
        # TODO: 实现批量选择功能
        InfoBar.warning(
            title='功能开发中',
            content='批量操作功能正在开发中',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )
    
    def on_batch_include(self):
        """批量恢复选中的壁纸"""
        # TODO: 实现批量选择功能
        InfoBar.warning(
            title='功能开发中',
            content='批量操作功能正在开发中',
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self
        )
    
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
    
    def highlight_item(self, index):
        """高亮显示指定索引的壁纸项 - 兼容性方法"""
        try:
            # 获取当前显示的项目列表
            items = []
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if isinstance(widget, ThumbnailWidget):
                    items.append(widget)
            
            # 清除所有高亮
            for item in items:
                item.setStyleSheet("")
            
            # 高亮指定项目
            if 0 <= index < len(items):
                item = items[index]
                item.setStyleSheet("ThumbnailWidget { border: 2px solid #0078d4; }")
                
        except Exception as e:
            print(f"高亮项目时出错: {e}")