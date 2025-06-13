import base64
from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal, QByteArray, QBuffer, QIODevice, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QScrollArea

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentIcon as FIF, NavigationItemPosition, CardWidget,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
                          setTheme, Theme, InfoBar, InfoBarPosition, FlowLayout, SearchLineEdit,
                          HyperlinkButton, TitleLabel, PushButton, ToolTipFilter,
                          PrimaryToolButton, TransparentPushButton, FluentStyleSheet)


class ThumbnailWidget(CardWidget):
    """单个缩略图小部件 - 使用FluentWidgets风格"""
    itemClicked = pyqtSignal(str)  # 修改：将 clicked 重命名为 itemClicked
    excludeClicked = pyqtSignal(str)  # 排除按钮信号
    includeClicked = pyqtSignal(str)  # 恢复按钮信号
    
    def __init__(self, filename, info, is_excluded=False, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.info = info
        self.is_excluded = is_excluded
        
        # 新增：连接基类信号到自定义处理函数
        self.clicked.connect(self._handle_click)
        
        # 设置基本属性
        self.setFixedSize(200, 200)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # 缩略图显示区域
        self.thumbnail_label = QWidget()
        self.thumbnail_label.setMinimumSize(180, 120)
        self.thumbnail_label.setObjectName("thumbnailContainer")
        
        thumb_layout = QVBoxLayout(self.thumbnail_label)
        thumb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = BodyLabel("")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_layout.addWidget(self.image_label)
        
        layout.addWidget(self.thumbnail_label)
        
        # 文件名标签
        display_name = info.get("display_name", filename)
        if len(display_name) > 20:
            display_name = display_name[:17] + "..."
            
        self.name_label = StrongBodyLabel(display_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setToolTip(filename)
        self.name_label.installEventFilter(ToolTipFilter(self.name_label))
        layout.addWidget(self.name_label)
        
        # # 使用CaptionLabel显示分辨率信息
        # if "resolution" in info:
        #     resolution = info["resolution"]
        # else:
        #     resolution = f"{info.get('width', '?')}x{info.get('height', '?')}"
            
        # self.info_label = CaptionLabel(resolution)
        # self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(self.info_label)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 4, 0, 0)
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 按钮: 排除/恢复
        if is_excluded:
            self.toggle_button = TransparentPushButton("恢复")
            self.toggle_button.setIcon(FIF.ACCEPT)
            self.toggle_button.setToolTip("将此壁纸从排除列表移除")
            self.toggle_button.clicked.connect(self._on_include_clicked)
            
            # 设置样式表示已排除
            self.setProperty("excluded", True)
            self.setStyle(self.style())
        else:
            self.toggle_button = TransparentPushButton("排除")
            self.toggle_button.setIcon(FIF.CANCEL)
            self.toggle_button.setToolTip("将此壁纸加入排除列表")
            self.toggle_button.clicked.connect(self._on_exclude_clicked)
            
            self.setProperty("excluded", False)
            self.setStyle(self.style())
        
        buttons_layout.addWidget(self.toggle_button)
        layout.addLayout(buttons_layout)
        
        # 设置样式表
        self._update_style()
        
        # 加载缩略图
        self._load_thumbnail()
    
    def _update_style(self):
        """更新样式表"""
        FluentStyleSheet.CARD_WIDGET.apply(self)
        
        if self.is_excluded:
            self.setStyleSheet("""
                CardWidget {
                    border-radius: 8px;
                    background-color: rgba(100, 100, 100, 30);
                }
                
                CardWidget:hover {
                    background-color: rgba(120, 120, 120, 50);
                }
                
                #thumbnailContainer {
                    background-color: rgba(0, 0, 0, 10);
                    border-radius: 4px;
                }
                               
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                CardWidget {
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 20);
                }
                
                CardWidget:hover {
                    background-color: rgba(200, 200, 200, 40);
                }
                
                #thumbnailContainer {
                    background-color: rgba(0, 0, 0, 10);
                    border-radius: 4px;
                }
                               
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: transparent;
                }
            """)
    
    def _load_thumbnail(self):
        """加载缩略图"""
        try:
            if "view_pic" in self.info and self.info["view_pic"]:
                # 从base64加载
                base64_data = self.info["view_pic"]
                pixmap = QPixmap()
                if pixmap.loadFromData(QByteArray.fromBase64(base64_data.encode())):
                    # 调整大小以适应标签
                    pixmap = pixmap.scaled(180, 120, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
                    # 设置缩略图
                    self.image_label.setPixmap(pixmap)
                else:
                    self.image_label.setText("加载失败\n无效的图片数据")
            elif "path" in self.info:
                # 从文件加载
                pixmap = QPixmap(self.info["path"])
                if not pixmap.isNull():
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
                    self.image_label.setPixmap(pixmap)
                else:
                    self.image_label.setText("加载失败\n无效的图片")
            else:
                self.image_label.setText("无图片路径")
        
        except Exception as e:
            # 加载失败时显示占位图
            self.image_label.setText(f"加载失败\n{str(e)}")
            print(f"加载缩略图时出错: {e}")
    
    def _on_exclude_clicked(self):
        """排除按钮点击事件"""
        self.excludeClicked.emit(self.filename)
    
    def _on_include_clicked(self):
        """恢复按钮点击事件"""
        self.includeClicked.emit(self.filename)
    
    def _handle_click(self):
        """处理基类的点击事件，转发带有文件名的信号"""
        # 只在缩略图区域内才发出信号
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        if self.thumbnail_label.geometry().contains(cursor_pos):
            self.itemClicked.emit(self.filename)
            

class GalleryInterface(QFrame):
    """图库界面 - 使用FlowLayout重构"""
    
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
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)
        
        # 顶部标题和控制区域
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        
        # 标题
        title_label = TitleLabel("壁纸图库")
        title_label.setObjectName("galleryTitle")
        header_layout.addWidget(title_label)
        
        # 控制区域
        controls_frame = QFrame()
        
        controls_frame.setObjectName("controlsFrame")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        controls_layout.setSpacing(8)
        
        # 筛选下拉框
        self.filter_combo = ComboBox()
        self.filter_combo.addItems(["所有壁纸", "已启用", "已排除"])
        self.filter_combo.setCurrentIndex(0)
        self.filter_combo.setMinimumWidth(100)
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        
        # 搜索框
        self.search_input = SearchLineEdit()
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
        self.refresh_button = PrimaryToolButton(FIF.SYNC)
        self.refresh_button.setToolTip("刷新图库")
        self.refresh_button.setFixedSize(36, 36)
        self.refresh_button.clicked.connect(self.refresh_gallery)
        
        # 添加控件到布局
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addWidget(self.search_input, 1)  # 搜索框占用更多空间
        controls_layout.addWidget(self.batch_exclude_button)
        controls_layout.addWidget(self.batch_include_button)
        controls_layout.addWidget(self.refresh_button)
        
        header_layout.addWidget(controls_frame)
        main_layout.addLayout(header_layout)
        
        # 创建滚动区域用于显示缩略图
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setObjectName("galleryScrollArea")
        
        # 创建流布局容器
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("galleryContent")

        # 设置为透明背景
        self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_content.setStyleSheet("#galleryContent { background-color: transparent; }")

        self.flow_layout = FlowLayout(self.scroll_content)
        self.flow_layout.setContentsMargins(16, 16, 16, 16)
        self.flow_layout.setHorizontalSpacing(12)
        self.flow_layout.setVerticalSpacing(12)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, 1)  # 让滚动区域可拉伸
        
        # 底部状态栏
        self.status_label = BodyLabel("准备就绪")
        self.status_label.setObjectName("statusLabel")
        main_layout.addWidget(self.status_label)
        
        # 设置样式表
        self._update_style()
    
    def _update_style(self):
        """更新样式表"""
        self.setStyleSheet("""
            #galleryTitle {
                font-size: 24px;
                font-weight: bold;
                padding-bottom: 8px;
            }
            
            #controlsFrame {
                background-color: rgba(255, 255, 255, 15);
                border-radius: 8px;
            }
            
            #galleryScrollArea {
                background-color: transparent;
                border: none;
            }
            
            #statusLabel {
                padding: 8px 0;
            }
        """)
    
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
            # 检查是否实际接收到数据
            data_received = wallpaper_data is not None and len(wallpaper_data) > 0
            
            if not data_received:
                print("警告: 收到空的壁纸数据")
                # 如果已有数据，保留不覆盖
                if not hasattr(self, 'wallpaper_data') or not self.wallpaper_data:
                    self.wallpaper_data = {}
            else:
                print(f"收到壁纸数据: {len(wallpaper_data)} 条")
                self.wallpaper_data = wallpaper_data
                
                # 获取已排除的壁纸列表
                self.excluded_files = {key for key, info in self.wallpaper_data.items() 
                                      if info.get("excluded", False)}
                print(f"已排除的壁纸: {len(self.excluded_files)} 个")
                
            # 无论如何都刷新显示
            self.refresh_display()
                
        except Exception as e:
            print(f"设置壁纸数据时出错: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"设置数据失败: {str(e)}")
    
    def refresh_display(self):
        """刷新显示"""
        try:
            # 清空现有内容
            self._clear_layout()
            
            # 过滤和排序数据
            filtered_data = self._filter_wallpaper_data()
            
            # 如果没有数据，显示提示
            if not filtered_data:
                self._show_empty_message()
                return
            
            # 排序 (按文件名)
            sorted_items = sorted(filtered_data.items(), key=lambda x: x[0])
            
            # 填充流布局
            self._populate_layout(sorted_items)
            
            # 更新状态
            self.status_label.setText(f"显示 {len(filtered_data)} 张壁纸 (共 {len(self.wallpaper_data)} 张)")
            
        except Exception as e:
            print(f"刷新显示时出错: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"刷新显示失败: {str(e)}")

    def _clear_layout(self):
        """清空布局"""
        try:
            # 先获取所有小部件引用
            widgets = []
            for i in range(self.flow_layout.count()):
                layout_item = self.flow_layout.itemAt(i)
                if layout_item and layout_item.widget():
                    widgets.append(layout_item.widget())
            
            # 清空布局
            for i in range(self.flow_layout.count()):
                self.flow_layout.takeAt(0)
            
            # 删除小部件
            for widget in widgets:
                widget.setParent(None)
                widget.deleteLater()
                
        except Exception as e:
            print(f"清空布局时出错: {e}")
            import traceback
            traceback.print_exc()
    
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
        empty_label = BodyLabel()
        empty_label.setObjectName("emptyLabel")
        
        if self.search_text:
            empty_label.setText(f"没有找到包含 '{self.search_text}' 的壁纸")
        elif self.filter_combo.currentIndex() == 1:
            empty_label.setText("没有已启用的壁纸")
        elif self.filter_combo.currentIndex() == 2:
            empty_label.setText("没有已排除的壁纸")
        else:
            empty_label.setText("没有壁纸数据\n请确保壁纸目录中有图片文件")
        
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet("""
            #emptyLabel {
                color: gray;
                font-size: 16px;
                padding: 50px;
            }
        """)
        
        self.flow_layout.addWidget(empty_label)
        self.status_label.setText("没有壁纸显示")
    
    def _populate_layout(self, sorted_items):
        """使用流布局填充缩略图"""
        for filename, info in sorted_items:
            is_excluded = info.get("excluded", False)
            thumbnail = ThumbnailWidget(filename, info, is_excluded)
            
            # 连接缩略图信号 - 使用新的信号名
            thumbnail.itemClicked.connect(self._on_thumbnail_clicked)
            thumbnail.excludeClicked.connect(self._on_exclude_wallpaper)
            thumbnail.includeClicked.connect(self._on_include_wallpaper)
            
            # 添加到流布局
            self.flow_layout.addWidget(thumbnail)
    
    def on_filter_changed(self):
        """筛选条件改变"""
        filter_names = ["all", "included", "excluded"]
        self.current_filter = filter_names[self.filter_combo.currentIndex()]
        self.refresh_display()
    
    def on_search_changed(self):
        """搜索文本改变"""
        # 使用定时器避免输入过程中的频繁刷新
        if hasattr(self, '_search_timer') and self._search_timer.isActive():
            self._search_timer.stop()
        else:
            self._search_timer = QTimer()
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(self._do_search)
        
        self._search_timer.start(300)  # 300ms 延迟
    
    def _do_search(self):
        """执行搜索"""
        self.search_text = self.search_input.text().strip()
        self.refresh_display()
    
    def _on_thumbnail_clicked(self, filename):
        """缩略图点击事件"""
        try:
            # 高亮选中的缩略图
            self.highlight_item(filename)
            
            # 发送信号
            self.wallpaperSelected.emit(filename)
            
            # 显示选中提示
            InfoBar.success(
                title='已选择',
                content=f'已选择壁纸: {filename}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=self
            )
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
            
            # 刷新显示 - 延迟执行以便用户看到反馈
            QTimer.singleShot(100, self.refresh_display)
            
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
            
            # 刷新显示 - 延迟执行以便用户看到反馈
            QTimer.singleShot(100, self.refresh_display)
            
        except Exception as e:
            print(f"恢复壁纸时出错: {e}")
            self.show_error(f"恢复壁纸失败: {str(e)}")
    
    def refresh_gallery(self):
        """刷新图库"""
        try:
            if hasattr(self.controller, 'refresh_gallery'):
                self.controller.refresh_gallery()
            elif hasattr(self.controller, 'open_gallery'):
                self.controller.open_gallery()
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
    
    def highlight_item(self, key):
        """高亮显示指定键的壁纸项"""
        try:
            # 获取当前显示的所有小部件
            found_items = []
            
            # 遍历布局中的所有项目
            for i in range(self.flow_layout.count()):
                layout_item = self.flow_layout.itemAt(i)
                # 确保获取的是小部件项
                if layout_item and layout_item.widget():
                    widget = layout_item.widget()
                    # 确保是ThumbnailWidget类型
                    if isinstance(widget, ThumbnailWidget):
                        found_items.append(widget)
            
            # 清除所有高亮
            for item in found_items:
                # 恢复正常样式
                item._update_style()
            
            # 找到匹配的项目并高亮
            for item in found_items:
                if item.filename == key:
                    # 设置高亮样式
                    item.setStyleSheet("""
                        CardWidget {
                            border: 2px solid #0078d4;
                            border-radius: 8px;
                            background-color: rgba(0, 120, 212, 0.1);
                        }
                        
                        CardWidget:hover {
                            background-color: rgba(0, 120, 212, 0.2);
                        }
                        
                        #thumbnailContainer {
                            background-color: rgba(0, 0, 0, 10);
                            border-radius: 4px;
                        }
                    """)
                    
                    # 滚动到该项目
                    if self.scroll_area:
                        self.scroll_area.ensureWidgetVisible(item)
                    break
                
        except Exception as e:
            print(f"高亮项目时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def showEvent(self, event):
        """在显示图库时自动加载数据"""
        super().showEvent(event)
        
        # 如果没有数据或数据为空，尝试加载
        if not self.wallpaper_data or len(self.wallpaper_data) == 0:
            print("图库自动加载数据...")
            
            # 尝试使用控制器加载数据
            if hasattr(self.controller, 'open_gallery'):
                QTimer.singleShot(100, self.controller.open_gallery)
            elif hasattr(self.controller, 'refresh_gallery'):
                QTimer.singleShot(100, self.controller.refresh_gallery)