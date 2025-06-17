import base64
from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal, QByteArray, QBuffer, QIODevice, QTimer, QThread
from PyQt6.QtGui import QIcon, QPixmap, QAction, QColor
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QScrollArea

# 导入QFluentWidgets组件
from qfluentwidgets import (FluentIcon as FIF, NavigationItemPosition, CardWidget,
                          ToolButton, PrimaryPushButton, TransparentToolButton, 
                          SwitchButton, ComboBox, SubtitleLabel, CaptionLabel, BodyLabel, StrongBodyLabel,
                          setTheme, Theme, InfoBar, InfoBarPosition, FlowLayout, SearchLineEdit,
                          HyperlinkButton, TitleLabel, PushButton, ToolTipFilter,
                          PrimaryToolButton, TransparentPushButton, FluentStyleSheet,
                          ElevatedCardWidget, ImageLabel, InfoBadge, SingleDirectionScrollArea)
from .ThumbnailWidget import ThumbnailWidget
from ..models.picture_item import Picture
from typing import Dict, List, Optional, Union

class GalleryInterface(QFrame):
    """图库界面 - 使用FlowLayout重构"""
    
    # 定义信号 - 修改为传递Picture对象或key
    wallpaperSelected = pyqtSignal(object)  # 发送选中的壁纸对象或key
    excludeWallpaper = pyqtSignal(object)   # 排除壁纸
    includeWallpaper = pyqtSignal(object)   # 恢复壁纸
    
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent)
        self.controller = controller
        self.setObjectName("Gallery-Interface")
        
        # 数据存储 - 修改为存储key与Picture对象的映射
        self.wallpaper_data = {}  # 存储所有壁纸数据: {key: Picture对象}
        self.excluded_files = set()  # 排除的壁纸key
        self.current_filter = "all"  # 当前筛选: all, included, excluded
        self.search_text = ""  # 搜索文本
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置图库界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)
        
        # 顶部标题和控制区域放在同一行
        header_layout = QHBoxLayout()  # 改为水平布局
        header_layout.setSpacing(12)
        
        # 标题 - 放在左侧
        title_label = TitleLabel("壁纸图库")
        title_label.setObjectName("galleryTitle")
        header_layout.addWidget(title_label)
        
        # 控制区域 - 放在右侧
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
        self.batch_exclude_button = PrimaryPushButton("排除")
        self.batch_exclude_button.setIcon(FIF.CANCEL)
        self.batch_exclude_button.clicked.connect(self.on_batch_exclude)
        
        self.batch_include_button = PrimaryPushButton("恢复")
        self.batch_include_button.setIcon(FIF.ACCEPT)
        self.batch_include_button.clicked.connect(self.on_batch_include)
        
        # 刷新按钮
        self.refresh_button = PrimaryToolButton(FIF.SYNC)
        self.refresh_button.setToolTip("刷新图库")
        self.refresh_button.clicked.connect(self.refresh_gallery)
        
        # 添加控件到布局
        controls_layout.addWidget(self.filter_combo)
        controls_layout.addWidget(self.search_input, 1)  # 搜索框占用更多空间
        controls_layout.addWidget(self.batch_exclude_button)
        controls_layout.addWidget(self.batch_include_button)
        controls_layout.addWidget(self.refresh_button)
        
        header_layout.addWidget(controls_frame, 1)  # 控制区域占据更多空间
        main_layout.addLayout(header_layout)
        
        # 创建滚动区域用于显示缩略图
        self.scroll_area = SingleDirectionScrollArea(orient=Qt.Orientation.Vertical)
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
        
        # 添加加载指示器
        self.loading_widget = InfoBadge.success(1)
        self.loading_widget.hide()
    
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
            if hasattr(self.controller, 'select_wallpaper'):
                self.wallpaperSelected.connect(self.controller.select_wallpaper)
            
            # 连接排除壁纸信号
            if hasattr(self.controller, 'exclude_wallpaper'):
                self.excludeWallpaper.connect(self.controller.exclude_wallpaper)
            
            # 连接恢复壁纸信号
            if hasattr(self.controller, 'include_wallpaper'):
                self.includeWallpaper.connect(self.controller.include_wallpaper)
                
        except Exception as e:
            print(f"连接信号时出错: {e}")
    
    def set_data(self, wallpaper_data):
        """设置壁纸数据
        
        Args:
            wallpaper_data (dict): 壁纸数据字典 {key: Picture对象}
        """
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
                
                # 获取已排除的壁纸列表 - 根据Picture对象的excluded属性
                self.excluded_files = {key for key, pic in self.wallpaper_data.items() 
                                      if pic.excluded}
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
            # 使用定时器延迟执行实际渲染，让UI有机会更新加载指示器
            QTimer.singleShot(50, lambda: self._perform_refresh_display())
            
        except Exception as e:
            print(f"刷新显示时出错: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"刷新显示失败: {str(e)}")

    def _perform_refresh_display(self):
        """执行实际的刷新显示操作"""
        try:
            # 过滤和排序数据
            filtered_data = self._filter_wallpaper_data()
            
            # 显示过滤后的数据
            self._display_wallpaper_data(filtered_data)
            
        except Exception as e:
            print(f"执行刷新显示时出错: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"刷新显示失败: {str(e)}")
        
    def _display_wallpaper_data(self, filtered_data):
        """显示壁纸数据到UI"""
        # 清空现有内容
        self._clear_layout()
    
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
        
        for key, picture in self.wallpaper_data.items():
            is_excluded = picture.excluded
            
            # 应用筛选
            filter_index = self.filter_combo.currentIndex()
            if filter_index == 1 and is_excluded:  # 只显示已启用
                continue
            elif filter_index == 2 and not is_excluded:  # 只显示已排除
                continue
                
            # 应用搜索
            if self.search_text:
                display_name = picture.display_name
                if (self.search_text.lower() not in display_name.lower() and 
                    self.search_text.lower() not in key.lower()):
                    continue
            
            filtered_data[key] = picture
        
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
        for key, picture in sorted_items:
            is_excluded = picture.excluded
            
            # 提供关键信息创建缩略图小部件
            thumbnail = ThumbnailWidget(key, picture, is_excluded=is_excluded)
            
            # 连接缩略图信号 - 使用新的信号名
            thumbnail.itemClicked.connect(self._on_thumbnail_clicked)
            thumbnail.excludeClicked.connect(self._on_exclude_wallpaper)
            thumbnail.includeClicked.connect(self._on_include_wallpaper)
            
            # 添加到流布局
            self.flow_layout.addWidget(thumbnail)
    
    def on_filter_changed(self):
        """筛选条件改变时异步刷新"""
        filter_names = ["all", "included", "excluded"]
        self.current_filter = filter_names[self.filter_combo.currentIndex()]
        
        # 立即执行刷新显示
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
        """执行搜索时异步刷新"""
        self.search_text = self.search_input.text().strip()
        
        # 立即执行刷新显示
        self.refresh_display()
    
    def _on_thumbnail_clicked(self, key):
        """缩略图点击事件
        
        Args:
            key (str): 壁纸的键
        """
        try:
            # 获取对应的Picture对象
            picture = self.wallpaper_data.get(key)
            if not picture:
                raise ValueError(f"找不到壁纸: {key}")
            
            # 发送信号 - 传递Picture对象
            self.wallpaperSelected.emit(picture)

        except Exception as e:
            # 处理点击错误
            print(f"缩略图点击处理出错: {e}")
            InfoBar.error(
                title='错误',
                content=f'处理缩略图点击时出错: {str(e)}',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
    
    def _on_exclude_wallpaper(self, key):
        """将壁纸添加到排除列表
        
        Args:
            key (str): 壁纸的键
        """
        try:
            # 获取对应的Picture对象
            picture = self.wallpaper_data.get(key)
            if not picture:
                raise ValueError(f"找不到壁纸: {key}")
            
            # 更新排除状态
            picture.set_excluded(True)
            self.excluded_files.add(key)
            
            # 发送信号 - 传递Picture对象
            self.excludeWallpaper.emit(picture)
            
            # 显示成功消息
            InfoBar.success(
                title='操作成功',
                content=f'已排除壁纸: {picture.display_name}',
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
    
    def _on_include_wallpaper(self, key):
        """将壁纸从排除列表移除
        
        Args:
            key (str): 壁纸的键
        """
        try:
            # 获取对应的Picture对象
            picture = self.wallpaper_data.get(key)
            if not picture:
                raise ValueError(f"找不到壁纸: {key}")
            
            # 更新排除状态
            picture.set_excluded(False)
            if key in self.excluded_files:
                self.excluded_files.remove(key)
            
            # 发送信号 - 传递Picture对象
            self.includeWallpaper.emit(picture)
            
            # 显示成功消息
            InfoBar.success(
                title='操作成功',
                content=f'已恢复壁纸: {picture.display_name}',
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
        """异步刷新图库"""
        try:
            # 获取当前筛选和搜索
            filter_names = ["all", "included", "excluded"]
            current_filter = filter_names[self.filter_combo.currentIndex()]
            search_text = self.search_input.text().strip()
            
            # 创建并启动异步线程
            self.refresh_thread = GalleryRefreshThread(
                self.controller,
                filter_text=search_text,
                filter_mode=current_filter
            )
            
            # 连接信号
            self.refresh_thread.finished.connect(self._on_refresh_complete)
            self.refresh_thread.error.connect(self._on_refresh_error)
            self.refresh_thread.progress.connect(self._on_refresh_progress)
            
            # 启动线程
            self.refresh_thread.start()
            
        except Exception as e:
            print(f"启动异步刷新时出错: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"刷新图库失败: {str(e)}")

    def _on_refresh_complete(self, data):
        """异步刷新完成回调"""
        try:
            # 更新数据
            if data:
                self.wallpaper_data = data
                
                # 获取已排除的壁纸列表
                self.excluded_files = {key for key, picture in self.wallpaper_data.items() 
                                      if picture.excluded}
            
            # 刷新UI显示
            self._display_wallpaper_data(data)
            
            # 显示成功消息
            InfoBar.success(
                title='刷新完成',
                content=f'图库已刷新，显示 {len(data)} 张壁纸',
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1500,
                parent=self
            )
            
        except Exception as e:
            print(f"处理异步刷新结果时出错: {e}")
            import traceback
            traceback.print_exc()
            self.show_error(f"刷新图库失败: {str(e)}")

    def _on_refresh_error(self, error_message):
        """异步刷新出错回调"""
        self.show_error(f"刷新图库失败: {error_message}")

    def _on_refresh_progress(self, progress):
        """更新异步刷新进度"""
        self.status_label.setText(f"正在刷新图库... {progress}%")
    
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
    
    def showEvent(self, event):
        """在显示图库时自动加载数据"""
        super().showEvent(event)
        
        # 确保加载指示器在正确位置
        if hasattr(self, 'loading_widget'):
            x = (self.width() - self.loading_widget.width()) // 2
            y = (self.height() - self.loading_widget.height()) // 2
            self.loading_widget.move(x, y)
    
        # 如果没有数据或数据为空，尝试加载
        if not self.wallpaper_data or len(self.wallpaper_data) == 0:
            print("图库自动加载数据...")
            
            # 尝试使用控制器加载数据
            QTimer.singleShot(100, lambda: self._load_initial_data())

    def _load_initial_data(self):
        """加载初始数据"""
        try:
            if hasattr(self.controller, 'open_gallery'):
                self.controller.open_gallery()
            elif hasattr(self.controller, 'refresh_gallery'):
                self.controller.refresh_gallery()
        except Exception as e:
            print(f"加载初始数据时出错: {e}")
            self.show_error(f"加载图库数据失败: {str(e)}")
            
# 添加刷新线程类
class GalleryRefreshThread(QThread):
    """异步刷新图库线程"""
    finished = pyqtSignal(dict)  # 完成信号，传递刷新后的数据 {key: Picture}
    error = pyqtSignal(str)      # 错误信号
    progress = pyqtSignal(int)   # 进度信号
    
    def __init__(self, controller, filter_text="", filter_mode="all"):
        super().__init__()
        self.controller = controller
        self.filter_text = filter_text
        self.filter_mode = filter_mode
    
    def run(self):
        """执行异步刷新"""
        try:
            # 获取壁纸数据
            if hasattr(self.controller, 'get_wallpaper_data'):
                wallpaper_data = self.controller.get_wallpaper_data()
                
                # 过滤数据(如果需要)
                filtered_data = {}
                total = len(wallpaper_data)
                
                for i, (key, picture) in enumerate(wallpaper_data.items()):
                    # 发送进度信号
                    self.progress.emit(int((i / total) * 100) if total > 0 else 0)
                    
                    # 应用过滤规则
                    is_excluded = picture.excluded
                    
                    # 应用筛选
                    if self.filter_mode == "included" and is_excluded:  # 只显示已启用
                        continue
                    elif self.filter_mode == "excluded" and not is_excluded:  # 只显示已排除
                        continue
                        
                    # 应用搜索
                    if self.filter_text:
                        display_name = picture.display_name
                        if (self.filter_text.lower() not in display_name.lower() and 
                            self.filter_text.lower() not in key.lower()):
                            continue
                    
                    filtered_data[key] = picture
                
                # 发送完成信号
                self.finished.emit(filtered_data)
                
            else:
                self.error.emit("控制器没有提供 get_wallpaper_data 方法")
                
        except Exception as e:
            import traceback
            print(f"异步刷新图库时出错: {e}")
            print(traceback.format_exc())
            self.error.emit(str(e))