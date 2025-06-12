import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import os
from screeninfo import get_monitors

from .components.crop_canvas import CropCanvas

class IndexBuilderUI:
    """索引构建器UI"""
    def __init__(self, manager, parent_window):
        self.manager = manager
        self.parent_window = parent_window
        self.progress_window = None
        self.progress_label = None
        self.progress_bar = None
        
    def build(self):
        """开始构建索引"""
        self._create_progress_window()
        try:
            success = self.manager.build_index(self._progress_callback)
            return success
        finally:
            if self.progress_window:
                self.progress_window.destroy()
                
    def _create_progress_window(self):
        """创建进度窗口"""
        self.progress_window = tk.Toplevel(self.parent_window)
        self.progress_window.title("构建索引")
        self.progress_window.geometry("500x120")
        self.progress_window.transient(self.parent_window)
        self.progress_window.grab_set()
        
        tk.Label(self.progress_window, text="正在构建壁纸索引...").pack(pady=10)
        self.progress_label = tk.Label(self.progress_window, text="准备中...")
        self.progress_label.pack()
        
        # 添加进度条（可选）
        try:
            from tkinter import ttk
            self.progress_bar = ttk.Progressbar(self.progress_window, mode='determinate')
            self.progress_bar.pack(pady=10, padx=20, fill=tk.X)
        except ImportError:
            self.progress_bar = None
    
    def _progress_callback(self, current, total, filename):
        """UI进度回调"""
        if self.progress_label:
            self.progress_label.config(text=f"处理中: {current+1}/{total} - {filename}")
        
        if self.progress_bar:
            self.progress_bar['maximum'] = total
            self.progress_bar['value'] = current + 1
        
        if self.progress_window:
            self.progress_window.update()

class WallpaperTkApp:
    def __init__(self, root, wallpaper_manager, file_utils, image_utils, realesrgan_tool):
        self.root = root
        self.manager = wallpaper_manager
        self.file_utils = file_utils
        self.image_utils = image_utils
        self.realesrgan = realesrgan_tool
        
        self.current_index = 0
        self.wallpaper_list = []
        self.excluded_files = set()
        self.random_seed = random.randint(1, 1000000)
        
        self.create_ui()
        self.initialize_data()
    
    def create_ui(self):
        self.root.title("壁纸预览与管理")
        
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 图片显示区域
        self.canvas = CropCanvas(main_frame, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 按钮框架
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # 按钮
        tk.Button(btn_frame, text="上一张", command=self.prev_wallpaper).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="下一张", command=self.next_wallpaper).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="应用裁剪", command=self.apply_crop).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="排除当前", command=self.exclude_wallpaper).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="刷新索引", command=self.refresh_index).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_label = tk.Label(main_frame, text="准备中...", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)
    
    def initialize_data(self):
        """初始化数据"""
        self.excluded_files = self.file_utils.get_excluded()
        
        # 检查是否需要重建索引
        if not self.manager.load_index() or self.need_rebuild_index():
            self.rebuild_index()
        
        self.wallpaper_list = [f for f in self.manager.get_wallpaper_list() 
                              if f not in self.excluded_files]
        
        if self.wallpaper_list:
            random.seed(self.random_seed)
            random.shuffle(self.wallpaper_list)
            # 延迟加载第一张图片，确保UI完全初始化
            self.root.after(50, self.load_wallpaper)
        else:
            messagebox.showerror("错误", "没有可用的壁纸!")
    
    def rebuild_index(self):
        """重建索引"""
        builder_ui = IndexBuilderUI(self.manager, self.root)
        if not builder_ui.build():
            messagebox.showerror("错误", "构建索引失败!")
    
    def need_rebuild_index(self):
        """检查是否需要重建索引"""
        if not os.path.exists(self.manager.config.WALLPAPER_DIR):
            return False
        
        current_mtime = os.path.getmtime(self.manager.config.WALLPAPER_DIR)
        last_mtime = self.manager.index_data.get("last_updated", 0)
        
        return current_mtime > last_mtime
    
    def load_wallpaper(self):
        """加载当前壁纸"""
        if not self.wallpaper_list:
            return
            
        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]
        
        try:
            # 加载图片
            img = Image.open(wallpaper_info["path"])
            
            # 强制更新canvas尺寸
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # 防止canvas尺寸为0
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600
            
            img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            
            # 清除画布并显示图片
            self.canvas.delete("all")
            self.canvas.create_image(
                canvas_width//2, canvas_height//2, 
                image=self.tk_img, anchor=tk.CENTER
            )
            
            # 自动设置为壁纸（使用缓存或原图）
            self.set_current_wallpaper()
            
            # 更新状态
            total = len(self.wallpaper_list)
            self.status_label.config(text=f"{filename} ({self.current_index+1}/{total})")
            self.root.title(f"壁纸管理 - {filename}")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败: {e}")
            self.exclude_wallpaper()
    
    def set_current_wallpaper(self):
        """设置当前壁纸（优先使用缓存）"""
        if not self.wallpaper_list:
            return

        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]

        # 优先使用缓存文件
        if wallpaper_info.get("cache_path") and wallpaper_info["cache_path"]:
            cache_path = os.path.join(self.manager.config.CACHE_DIR, wallpaper_info["cache_path"])
            if os.path.exists(cache_path):
                self.manager.set_wallpaper(cache_path)
                return
        
        # 使用原图
        self.manager.set_wallpaper(wallpaper_info["path"])
    
    def prev_wallpaper(self):
        """上一张壁纸"""
        if self.wallpaper_list:
            self.current_index = (self.current_index - 1) % len(self.wallpaper_list)
            self.load_wallpaper()
    
    def next_wallpaper(self):
        """下一张壁纸"""
        if self.wallpaper_list:
            self.current_index = (self.current_index + 1) % len(self.wallpaper_list)
            self.load_wallpaper()
    
    def apply_crop(self):
        """应用裁剪"""
        if not self.wallpaper_list or not self.canvas.crop_region:
            messagebox.showwarning("警告", "请先选择裁剪区域")
            return
            
        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]
        
        try:
            # 计算实际裁剪坐标
            img = Image.open(wallpaper_info["path"])
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # 计算缩放比例
            img_ratio = min(canvas_width / img.width, canvas_height / img.height)
            display_width = int(img.width * img_ratio)
            display_height = int(img.height * img_ratio)
            
            # 计算偏移
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2
            
            # 转换裁剪坐标
            crop_x, crop_y, crop_w, crop_h = self.canvas.crop_region
            crop_x = max(0, (crop_x - offset_x) / img_ratio)
            crop_y = max(0, (crop_y - offset_y) / img_ratio)
            crop_w = min(img.width - crop_x, crop_w / img_ratio)
            crop_h = min(img.height - crop_y, crop_h / img_ratio)
            
            # 裁剪图片
            cropped = img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
            
            # 保存裁剪后的图片到临时路径
            name, ext = os.path.splitext(filename)
            cache_filename = f"cropped_{name}{ext}"
            cache_path = os.path.join(self.manager.config.CACHE_DIR, cache_filename)
            cropped.save(cache_path)

            # 获取屏幕分辨率
            screen_width, screen_height = get_monitors()[0].width, get_monitors()[0].height

            # 调整图片适配屏幕
            final_filename = f"fit_{name}{ext}"
            final_cache_path = os.path.join(self.manager.config.CACHE_DIR, final_filename)
            
            # 根据需要缩小或放大图片
            if cropped.width > 2*screen_width or cropped.height > 2*screen_height:
                # 缩小
                self.image_utils.fit_image_to_screen(cache_path, final_cache_path, screen_width, screen_height)
            elif cropped.width < screen_width or cropped.height < screen_height:
                # 放大，使用realesrgan
                self.realesrgan.fit_to_screen(cache_path, final_cache_path, screen_width, screen_height)
            else:
                # 尺寸合适，直接复制
                cropped.save(final_cache_path)

            # 更新索引
            self.manager.update_crop_region(filename, [crop_x, crop_y, crop_w, crop_h], final_filename)
            
            # 设置为壁纸 - 立即设置，无需异步
            self.manager.set_wallpaper(final_cache_path, async_mode=False)
            
            # 清除裁剪框
            self.canvas.crop_region = None
            if self.canvas.rect_id:
                self.canvas.delete(self.canvas.rect_id)
                self.canvas.rect_id = None
            
            messagebox.showinfo("成功", "裁剪并设置壁纸成功!")
            
        except Exception as e:
            messagebox.showerror("错误", f"裁剪失败: {e}")
    
    def exclude_wallpaper(self):
        """排除当前壁纸"""
        if self.wallpaper_list:
            filename = self.wallpaper_list[self.current_index]
            self.excluded_files.add(filename)
            self.file_utils.add_to_excluded(filename)
            self.wallpaper_list.remove(filename)
            
            if self.wallpaper_list:
                self.current_index = self.current_index % len(self.wallpaper_list)
                self.load_wallpaper()
            else:
                messagebox.showinfo("提示", "没有更多壁纸了!")
    
    def refresh_index(self):
        """刷新索引"""
        self.rebuild_index()
        self.initialize_data()
        messagebox.showinfo("完成", f"索引已刷新! 找到 {len(self.wallpaper_list)} 张可用壁纸")