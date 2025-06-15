from PyQt6.QtCore import QObject, pyqtSlot, QTimer
from qfluentwidgets import setTheme, Theme
import os
import sys
import winreg as reg
from ..views.dialogs import ProgressDialog, show_error, show_info
import threading, time
import random

from .. import wallpaperCfg

class WallpaperController(QObject):
    """壁纸管理控制器，处理业务逻辑"""
    
    def __init__(self, model, image_utils, realesrgan_tool):
        super().__init__()
        self.model = model
        self.image_utils = image_utils
        self.realesrgan = realesrgan_tool
        self.view = None  # Will be set later

        # 连接模型信号
        self.model.currentWallpaperChanged.connect(self._on_wallpaper_changed)
        
        # 创建定时器用于自动随机切换壁纸
        self.auto_change_timer = QTimer(self)
        self.auto_change_timer.timeout.connect(self.random_wallpaper)
        
        # 根据配置设置定时器
        interval = wallpaperCfg.wallpaperChangeInterval.value
        if interval > 0:
            # 将分钟转换为毫秒
            self.auto_change_timer.start(interval * 60 * 1000)

    def set_view(self, view):
        """设置视图"""
        self.view = view
    
    def initialize(self):
        """初始化应用"""
        # 加载索引
        if not self.model.load_index():
            if not self.rebuild_index():
                show_error(self.view, "错误", "构建索引失败!")
                return False
                
        # 如果没有壁纸
        if not self.model.filtered_keys:
            show_error(self.view, "错误", "没有可用的壁纸!")
            return True
        
        # 随机选择一张壁纸而不是总是从第一张开始
        if self.model.filtered_keys:
            random_key = random.choice(self.model.filtered_keys)
            self.model.set_current_key(random_key)
            
            # 异步生成缩略图
            self.generate_thumbnails_batch()
        
        return True
    
    def rebuild_index(self):
        """重建索引"""
        dlg = ProgressDialog(self.view, "构建索引", "正在构建壁纸索引...")
        
        # 连接信号
        def progress_callback(current, total, filename):
            dlg.update_progress(current, total, os.path.basename(filename))
        
        success = self.model.build_index(progress_callback)
        if not success:
            show_error(self.view, "错误", "构建索引失败!")
            
        return success
    
    @pyqtSlot()
    def refresh_index(self):
        """刷新索引"""
        if not self.rebuild_index():
            return
        
        # 如果有壁纸，选择第一张
        if self.model.filtered_keys:
            self.model.set_current_key(self.model.filtered_keys[0])
            show_info(self.view, "完成", f"索引已刷新! 找到 {len(self.model.filtered_keys)} 张可用壁纸")
        else:
            show_info(self.view, "提示", "未找到可用的壁纸!")
    
    @pyqtSlot()
    def next_wallpaper(self):
        """下一张壁纸"""
        self.model.next_wallpaper()
    
    @pyqtSlot()
    def prev_wallpaper(self):
        """上一张壁纸"""
        self.model.prev_wallpaper()
    
    @pyqtSlot()
    def exclude_current(self):
        """排除当前壁纸"""
        if not self.model.exclude_current_wallpaper() and not self.model.filtered_keys:
            show_info(self.view, "提示", "没有更多壁纸了!")
    
    @pyqtSlot(object)
    def apply_crop(self, crop_rect=None):
        """应用裁剪"""
        if not self.model.filtered_keys:
            show_error(self.view, "错误", "没有加载壁纸")
            return
            
        # 如果没有传递裁剪矩形，尝试从视图获取
        if not crop_rect:
            crop_rect = self.view.getCropRect()
            
        if not crop_rect:
            show_error(self.view, "警告", "请先选择裁剪区域")
            return
            
        key, info = self.model.get_current_wallpaper()
        if not key or not info:
            return
            
        try:
            from PyQt6.QtGui import QImage
            from PyQt6.QtCore import QRectF
            from screeninfo import get_monitors
            
            # 加载原图
            original_img = QImage(info["path"])
            
            # 获取缩放比例 - 需要场景大小
            scene_rect = self.view.homeInterface.image_view.scene.sceneRect()
            print(f"Scene Rect: {scene_rect}")
            
            # 计算缩放比例
            scale_x = original_img.width() / scene_rect.width()
            scale_y = original_img.height() / scene_rect.height()
            print(f"Scale: {scale_x}, {scale_y}")

            # 计算实际裁剪区域
            crop_x = crop_rect.x() * scale_x
            crop_y = crop_rect.y() * scale_y
            crop_w = crop_rect.width() * scale_x
            crop_h = crop_rect.height() * scale_y
            print(f"Crop Rect: {crop_x}, {crop_y}, {crop_w}, {crop_h}")
            
            # 确保裁剪区域在图像范围内
            crop_x = max(0, min(crop_x, original_img.width() - 1))
            crop_y = max(0, min(crop_y, original_img.height() - 1))
            crop_w = max(1, min(crop_w, original_img.width() - crop_x))
            crop_h = max(1, min(crop_h, original_img.height() - crop_y))
            
            # 裁剪图片
            cropped_img = original_img.copy(int(crop_x), int(crop_y), int(crop_w), int(crop_h))
            
            # 保存裁剪后的图片
            name, ext = os.path.splitext(os.path.basename(info["path"]))
            cache_filename = f"cropped_{name}{ext}"
            cache_path = os.path.join(wallpaperCfg.cacheDir.value, cache_filename)
            cropped_img.save(cache_path)
            
            # 获取屏幕分辨率
            screen_width, screen_height = get_monitors()[0].width, get_monitors()[0].height
            
            # 调整图片适配屏幕
            final_filename = f"fit_{name}{ext}"
            final_cache_path = os.path.join(wallpaperCfg.cacheDir.value, final_filename)
            
            # 根据需要缩小或放大图片
            if cropped_img.width() > 2*screen_width or cropped_img.height() > 2*screen_height:
                # 缩小
                self.image_utils.fit_image_to_screen(cache_path, final_cache_path, screen_width, screen_height)
            elif cropped_img.width() < screen_width or cropped_img.height() < screen_height:
                # 放大，使用realesrgan
                self.realesrgan.fit_to_screen(cache_path, final_cache_path, screen_width, screen_height)
            else:
                # 尺寸合适，直接保存
                cropped_img.save(final_cache_path)
            
            # 更新索引
            crop_region = {"x": crop_x, "y": crop_y, "width": crop_w, "height": crop_h}
            self.model.update_crop_region(key, crop_region, final_filename)
            
            # 设置为壁纸
            self.model.set_wallpaper(final_cache_path, async_mode=False)
            
        except Exception as e:
            show_error(self.view, "错误", f"裁剪失败: {str(e)}")
        
        # 裁剪完成后清除矩形
        # self.view.clearCropRect()
    
    def _on_wallpaper_changed(self, key, info):
        """当前壁纸变化处理"""
        if self.view:
            self.view.update_wallpaper(key, info)
            self.model.set_current_wallpaper()
    
    def open_gallery(self):
        """打开图库视图"""
        # 获取所有壁纸数据 (包括已排除)
        wallpaper_data = self.get_wallpaper_data()
        
        # 通知视图打开图库
        if hasattr(self.view, "show_gallery"):
            self.view.show_gallery(wallpaper_data)
        elif hasattr(self.view, "galleryInterface"):
            self.view.galleryInterface.set_data(wallpaper_data)

    @pyqtSlot(str)
    @pyqtSlot()  # 添加一个无参数的重载
    def exclude_wallpaper(self, key=None):
        """排除壁纸
        
        Args:
            key (str, optional): 要排除的壁纸键。如果为None，则排除当前壁纸。
        """
        if key is None:
            # 排除当前壁纸
            if not self.model.exclude_current_wallpaper() and not self.model.filtered_keys:
                show_info(self.view, "提示", "没有更多壁纸了!")
        else:
            # 排除指定壁纸
            if self.model.exclude_wallpaper(key):
                from os.path import basename
                # 使用正确的方法获取壁纸信息
                key_info = self.model.get_wallpaper(key)  # 修改这里
                if key_info:
                    name = basename(key_info.get("path", key))
                else:
                    name = key
                # show_info(self.view, "已排除", f"壁纸 {name} 已被排除")
    
    @pyqtSlot(str)
    def include_wallpaper(self, key):
        """恢复被排除的壁纸"""
        if self.model.include_wallpaper(key):
            from os.path import basename
            # 使用正确的方法获取壁纸信息
            key_info = self.model.get_wallpaper(key)  # 修改这里
            if key_info:
                name = basename(key_info.get("path", key))
            else:
                name = key
            # show_info(self.view, "已恢复", f"壁纸 {name} 已恢复使用")

    @pyqtSlot(str)
    def select_wallpaper_from_gallery(self, key):
        """从图库中选择壁纸"""
        # 检查壁纸是否存在
        key_info = self.model.get_wallpaper(key)  # 修改这里
        if not key_info:
            return
        
        # 如果壁纸被排除，则首先恢复它
        if key_info.get("excluded", False):
            self.model.include_wallpaper(key)
        
        # 设置为当前壁纸
        if self.model.set_current_key(key):
            # 关闭图库视图
            if hasattr(self.view, "close_gallery"):
                self.view.close_gallery()

    def generate_thumbnails_batch(self, batch_size=40):
        """分批生成缩略图"""
        # 获取所有没有缩略图的壁纸
        wallpapers = self.model.get_all_wallpapers()
        need_thumbnail = [key for key, info in wallpapers.items() 
                        if not info.get("view_pic")]
        
        # 优先处理非排除的壁纸
        active_wallpapers = [k for k in need_thumbnail if not wallpapers[k].get("excluded", False)]
        excluded_wallpapers = [k for k in need_thumbnail if wallpapers[k].get("excluded", False)]
        prioritized_list = active_wallpapers + excluded_wallpapers
        
        total = len(prioritized_list)
        if total == 0:
            return
        
        # 状态更新函数
        def update_status(current, total):
            if self.view and hasattr(self.view, "statusBar"):
                self.view.statusBar().showMessage(f"正在生成缩略图: {current}/{total}")
                if current >= total:
                    self.view.statusBar().showMessage("缩略图生成完成", 3000)  # 显示3秒
        
        def worker():
            for i in range(0, total, batch_size):
                # 处理一批
                batch = prioritized_list[i:i+batch_size]
                for key in batch:
                    self.model.get_thumbnail(key)
                
                # 更新状态
                current = min(i + batch_size, total)
                update_status(current, total)
                
                # 每批之间暂停一小段时间，避免占用太多资源
                time.sleep(0.1)
        
        # 开始处理第一批，显示初始状态
        update_status(0, total)
        
        # 启动后台线程
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    def generate_thumbnail_for_file(self, key):
        """为指定文件生成缩略图（可用于在视图中按需生成）"""
        if key in self.model.manager.index.wallpapers:
            thumbnail = self.model.get_thumbnail(key)
            return thumbnail is not None
        return False
    
    def set_auto_start(self, enabled):
        """设置开机自启动
        
        Args:
            enabled (bool): 是否启用自启动
        """
        try:
            # 获取程序路径
            app_path = os.path.abspath(sys.argv[0])
            
            # 如果是 Python 脚本，转换为可执行格式
            if app_path.endswith('.py'):
                # 使用 pythonw.exe 来运行，避免显示控制台
                python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                app_path = f'"{python_exe}" "{app_path}"'
            
            # 注册表路径
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            
            # 打开注册表项
            with reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_SET_VALUE) as key:
                if enabled:
                    # 设置自启动
                    reg.SetValueEx(key, "WallpaperManager", 0, reg.REG_SZ, app_path)
                    print(f"已设置自启动: {app_path}")
                else:
                    # 尝试删除自启动项
                    try:
                        reg.DeleteValue(key, "WallpaperManager")
                        print("已删除自启动设置")
                    except FileNotFoundError:
                        # 如果键不存在就忽略
                        pass
                
            return True
        
        except Exception as e:
            print(f"设置自启动时出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    @pyqtSlot()
    def settings_changed(self):
        """当设置变更时的处理函数"""
        # 获取配置
        config = wallpaperCfg
        
        # 重新启动自动切换计时器
        interval = config.wallpaperChangeInterval.value
        if hasattr(self, 'auto_change_timer'):
            if interval > 0:
                # 将分钟转换为毫秒
                self.auto_change_timer.start(interval * 60 * 1000)
            else:
                self.auto_change_timer.stop()
        
        # 应用自启动设置
        if hasattr(config, 'AUTO_START'):
            self.set_auto_start(config.autoStart.value)
        
        # 应用托盘设置
        # ...
        
        # 显示提示信息
        if self.view and hasattr(self.view, "statusBar"):
            self.view.statusBar().showMessage("设置已应用", 3000)

    @pyqtSlot()
    def random_wallpaper(self):
        """随机选择一张壁纸"""
        if not self.model.filtered_keys:
            # 使用 InfoBar 显示错误
            if self.view:
                from qfluentwidgets import InfoBar, InfoBarPosition
                from PyQt6.QtCore import Qt
                InfoBar.error(
                    title='错误',
                    content='没有可用的壁纸!',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self.view
                )
            return
        
        # 使用模型的随机壁纸功能
        self.model.random_wallpaper()
        
        # 更新状态栏 - 改为使用 info_label
        if self.view and hasattr(self.view, 'info_label'):
            total_count = len(self.model.filtered_keys)
            current_index = self.model.get_current_index() + 1  # 从1开始计数
            self.view.info_label.setText(f"随机显示第 {current_index}/{total_count} 张壁纸")

    def get_wallpaper_info(self, key):
        """获取壁纸信息"""
        return self.model.get_wallpaper_info(key)

    @pyqtSlot()
    def refresh_gallery(self):
        """刷新图库"""
        # 使用新方法获取壁纸数据
        wallpaper_data = self.get_wallpaper_data()
        
        # 检查是否有数据
        if not wallpaper_data:
            print("没有可用的壁纸数据")
            
            # 显示错误提示
            if self.view:
                from qfluentwidgets import InfoBar, InfoBarPosition
                from PyQt6.QtCore import Qt
                InfoBar.error(
                    title='错误',
                    content='没有可用的壁纸数据',
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self.view
                )
        
        # 更新图库数据
        if hasattr(self.view, "galleryInterface"):
            self.view.galleryInterface.set_data(wallpaper_data)

    def get_wallpaper_data(self):
        """获取所有壁纸数据
    
        Returns:
            dict: 包含所有壁纸信息的字典，键为文件名，值为壁纸信息
        """
        try:
            # 从模型中获取所有壁纸数据
            wallpaper_data = self.model.get_all_wallpapers()
            
            # 如果数据为空，尝试重建索引
            if not wallpaper_data and hasattr(self.model, 'load_index'):
                print("壁纸数据为空，尝试重新加载索引...")
                self.model.load_index()
                wallpaper_data = self.model.get_all_wallpapers()
            
            # 如果仍然为空，打印调试信息
            if not wallpaper_data:
                print("警告：获取到的壁纸数据为空")
            else:
                print(f"获取到 {len(wallpaper_data)} 条壁纸数据")
            
            return wallpaper_data
        except Exception as e:
            print(f"获取壁纸数据时出错: {e}")
            import traceback
            traceback.print_exc()
            return {}