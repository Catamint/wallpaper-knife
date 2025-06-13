from PyQt6.QtCore import QObject, pyqtSlot
import os
from ..views.dialogs import ProgressDialog, show_error, show_info
import threading, time

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
    
    def set_view(self, view):
        """设置视图"""
        self.view = view
    
    def initialize(self):
        """初始化应用"""
        # 加载索引
        if not self.model.load_index() or self.model.need_rebuild_index():
            if not self.rebuild_index():
                show_error(self.view, "错误", "构建索引失败!")
                return False
                
        # 初始化数据
        self.model.initialize()
        self.generate_thumbnails_batch()  # 异步生成缩略图    
            
        if not self.model.wallpaper_list:
            show_error(self.view, "错误", "没有可用的壁纸!")
            return True
            
        # 加载第一张壁纸
        self.model.set_current_index(0)
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
            
        self.model.initialize()
        
        if self.model.wallpaper_list:
            self.model.set_current_index(0)
            show_info(self.view, "完成", f"索引已刷新! 找到 {len(self.model.wallpaper_list)} 张可用壁纸")
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
    def exclude_wallpaper(self):
        """排除当前壁纸"""
        if not self.model.exclude_current_wallpaper() and not self.model.wallpaper_list:
            show_info(self.view, "提示", "没有更多壁纸了!")
    
    @pyqtSlot(object)
    def apply_crop(self, crop_rect=None):
        """应用裁剪"""
        if not self.model.wallpaper_list:
            show_error(self.view, "错误", "没有加载壁纸")
            return
            
        # 如果没有传递裁剪矩形，尝试从视图获取
        if not crop_rect:
            crop_rect = self.view.image_view.getCropRect()
            
        if not crop_rect:
            show_error(self.view, "警告", "请先选择裁剪区域")
            return
            
        filename, info = self.model.get_current_wallpaper()
        if not filename or not info:
            return
            
        try:
            from PyQt6.QtGui import QImage
            from PyQt6.QtCore import QRectF
            from screeninfo import get_monitors
            
            # 加载原图
            original_img = QImage(info["path"])
            
            # 获取缩放比例 - 需要场景大小
            scene_rect = self.view.image_view.scene.sceneRect()
            
            # 计算缩放比例
            scale_x = original_img.width() / scene_rect.width()
            scale_y = original_img.height() / scene_rect.height()
            
            # 计算实际裁剪区域
            crop_x = crop_rect.x() * scale_x
            crop_y = crop_rect.y() * scale_y
            crop_w = crop_rect.width() * scale_x
            crop_h = crop_rect.height() * scale_y
            
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
            cache_path = os.path.join(self.model.manager.config.CACHE_DIR, cache_filename)
            cropped_img.save(cache_path)
            
            # 获取屏幕分辨率
            screen_width, screen_height = get_monitors()[0].width, get_monitors()[0].height
            
            # 调整图片适配屏幕
            final_filename = f"fit_{name}{ext}"
            final_cache_path = os.path.join(self.model.manager.config.CACHE_DIR, final_filename)
            
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
            self.model.update_crop_region(filename, [crop_x, crop_y, crop_w, crop_h], final_filename)
            
            # 设置为壁纸
            self.model.set_wallpaper(final_cache_path, async_mode=False)
            
            # show_info(self.view, "成功", "裁剪并设置壁纸成功!")
            
        except Exception as e:
            show_error(self.view, "错误", f"裁剪失败: {str(e)}")
        
        # 裁剪完成后清除矩形
        self.view.image_view.clearCropRect()
    
    def _on_wallpaper_changed(self, filename, info):
        """当前壁纸变化处理"""
        if self.view:
            self.view.update_wallpaper(filename, info)
            self.model.set_current_wallpaper()
    
    def open_gallery(self):
        """打开图库视图"""
        # 获取所有壁纸数据 (包括已排除)
        wallpaper_data = self.model.get_all_wallpapers()
        
        # 通知视图打开图库 - 只传递壁纸数据，不再需要单独的排除列表
        if hasattr(self.view, "show_gallery"):
            self.view.show_gallery(wallpaper_data)

    @pyqtSlot(str)
    @pyqtSlot()  # 添加一个无参数的重载
    def exclude_wallpaper(self, filename=None):
        """排除壁纸
        
        Args:
            filename (str, optional): 要排除的壁纸文件名。如果为None，则排除当前壁纸。
        """
        if filename is None:
            # 排除当前壁纸
            if not self.model.exclude_current_wallpaper() and not self.model.wallpaper_list:
                show_info(self.view, "提示", "没有更多壁纸了!")
        else:
            # 排除指定壁纸
            if self.model.exclude_wallpaper(filename):
                from os.path import basename
                show_info(self.view, "已排除", f"壁纸 {basename(filename)} 已被排除")
    
    @pyqtSlot(str)
    def include_wallpaper(self, filename):
        """恢复被排除的壁纸"""
        if self.model.include_wallpaper(filename):
            from os.path import basename
            show_info(self.view, "已恢复", f"壁纸 {basename(filename)} 已恢复使用")

    @pyqtSlot(str)
    def select_wallpaper_from_gallery(self, filename):
        """从图库中选择壁纸"""
        # 检查壁纸是否被排除
        wallpaper_info = self.model.get_all_wallpapers().get(filename, {})
        
        # 如果壁纸被排除，则首先恢复它
        if wallpaper_info.get("excluded", False):
            self.model.include_wallpaper(filename)
        
        # 设置为当前壁纸
        if self.model.set_current_by_filename(filename):
            # 关闭图库视图
            if hasattr(self.view, "close_gallery"):
                self.view.close_gallery()

    
    def generate_thumbnails_batch(self, batch_size=40):
        """分批生成缩略图"""
        # 获取所有没有缩略图的壁纸
        wallpapers = self.model.get_all_wallpapers()
        need_thumbnail = [filename for filename, info in wallpapers.items() 
                        if not info.get("view_pic")]
        
        # 优先处理非排除的壁纸
        active_wallpapers = [f for f in need_thumbnail if not wallpapers[f].get("excluded", False)]
        excluded_wallpapers = [f for f in need_thumbnail if wallpapers[f].get("excluded", False)]
        prioritized_list = active_wallpapers + excluded_wallpapers
        
        total = len(prioritized_list)
        if total == 0:
            return
        
        # 状态更新函数
        def update_status(current, total):
            if self.view:
                self.view.statusBar().showMessage(f"正在生成缩略图: {current}/{total}")
                if current >= total:
                    self.view.statusBar().showMessage("缩略图生成完成", 3000)  # 显示3秒
        
        def worker():
            for i in range(0, total, batch_size):
                # 处理一批
                batch = prioritized_list[i:i+batch_size]
                for filename in batch:
                    self.model.manager.get_thumbnail_base64(filename)
                
                # 更新状态
                current = min(i + batch_size, total)
                update_status(current, total)
                
                # 保存索引
                self.model.manager.save_index()
                
                # 每批之间暂停一小段时间，避免占用太多资源
                time.sleep(0.1)
        
        # 开始处理第一批，显示初始状态
        update_status(0, total)
        
        # 启动后台线程
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    def generate_thumbnail_for_file(self, filename):
        """为指定文件生成缩略图（可用于在视图中按需生成）"""
        if filename in self.model.get_all_wallpapers():
            thumbnail = self.model.manager.get_thumbnail_base64(filename)
            return thumbnail is not None
        return False
    
    def settings_changed(self):
        """响应设置更改"""
        # 重新加载壁纸列表 (如果壁纸目录改变了)
        if self.view:
            self.view.statusBar().showMessage("正在应用新设置...")
            
        # 可能需要根据设置变化执行其他操作
        # 例如，如果壁纸目录改变，可能需要重建索引
        config = self.model.manager.config
        
        # 重新启动自动切换计时器(如果有)
        interval = config.WALLPAPER_CHANGE_INTERVAL
        if hasattr(self, 'auto_change_timer'):
            if interval > 0:
                # 将分钟转换为毫秒
                self.auto_change_timer.start(interval * 60 * 1000)
            else:
                self.auto_change_timer.stop()
        
        if self.view:
            self.view.statusBar().showMessage("设置已应用", 3000)