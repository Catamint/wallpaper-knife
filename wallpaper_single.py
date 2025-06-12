import os
import json
import hashlib
import random
import ctypes
import tkinter as tk
from tkinter import messagebox, Canvas
from PIL import Image, ImageTk
import threading
import time
import subprocess
from screeninfo import get_monitors

# 配置
WALLPAPER_DIR = r'C:\Users\kaika\OneDrive\图片\#插画'
INDEX_FILE = 'wallpaper_index.json'
CACHE_DIR = 'wallpaper_cache'
EXCLUDE_FILE = 'excluded.txt'

# 获取屏幕分辨率
def get_screen_size():
    monitor = get_monitors()[0]
    return monitor.width, monitor.height

# 获取脚本目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def calculate_file_hash(filepath):
    """计算文件MD5哈希值"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def get_excluded():
    exclude_path = os.path.join(BASE_DIR, EXCLUDE_FILE)
    if not os.path.exists(exclude_path):
        return set()
    try:
        with open(exclude_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except Exception as e:
        print(f"读取排除文件失败: {e}")
        return set()

def add_to_excluded(filename):
    exclude_path = os.path.join(BASE_DIR, EXCLUDE_FILE)
    try:
        with open(exclude_path, 'a', encoding='utf-8') as f:
            f.write(filename + '\n')
    except Exception as e:
        print(f"写入排除文件失败: {e}")

def set_wallpaper(image_path):
    try:
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
    except Exception as e:
        print(f"设置壁纸失败: {e}")

class WallpaperManager:
    def __init__(self):
        self.index_data = {
            "wallpapers": {},
            "total_count": 0,
            "last_updated": None
        }
        
    def build_index(self, progress_callback=None):
        """构建壁纸索引 - 逻辑分离版本"""
        if not os.path.exists(WALLPAPER_DIR):
            return False
            
        # 确保缓存目录存在
        cache_full_path = os.path.join(BASE_DIR, CACHE_DIR)
        os.makedirs(cache_full_path, exist_ok=True)
        
        # 加载旧索引
        old_index = {}
        if os.path.exists(os.path.join(BASE_DIR, INDEX_FILE)):
            try:
                with open(os.path.join(BASE_DIR, INDEX_FILE), 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                    old_index = old_data.get("wallpapers", {})
            except Exception as e:
                print(f"加载旧索引失败: {e}")
        
        # 扫描图片文件
        image_files = [f for f in os.listdir(WALLPAPER_DIR) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
        
        new_wallpapers = {}
        
        for i, filename in enumerate(image_files):
            if progress_callback:
                progress_callback(i, len(image_files), filename)
                
            filepath = os.path.join(WALLPAPER_DIR, filename)
            file_hash = calculate_file_hash(filepath)
            
            if file_hash:
                # 检查是否在旧索引中存在相同hash的文件
                existing_data = None
                for old_filename, old_data in old_index.items():
                    if old_data.get("hash") == file_hash:
                        existing_data = old_data.copy()
                        # 更新路径（文件可能被重命名）
                        existing_data["path"] = filepath
                        break
                
                if existing_data:
                    # 继承旧属性
                    new_wallpapers[filename] = existing_data
                    # 验证缓存文件是否存在
                    if existing_data.get("cache_path"):
                        cache_full_path_file = os.path.join(BASE_DIR, CACHE_DIR, existing_data["cache_path"])
                        if not os.path.exists(cache_full_path_file):
                            existing_data["cache_path"] = None
                            existing_data["crop_region"] = None
                else:
                    # 新文件
                    new_wallpapers[filename] = {
                        "hash": file_hash,
                        "path": filepath,
                        "crop_region": None,
                        "cache_path": None
                    }
        
        self.index_data["wallpapers"] = new_wallpapers
        self.index_data["total_count"] = len(new_wallpapers)
        self.index_data["last_updated"] = os.path.getmtime(WALLPAPER_DIR)
        
        self.save_index()
        return True
    
    def load_index(self):
        """加载索引文件"""
        index_path = os.path.join(BASE_DIR, INDEX_FILE)
        if not os.path.exists(index_path):
            return False
            
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                self.index_data = json.load(f)
            return True
        except Exception as e:
            print(f"加载索引失败: {e}")
            return False
    
    def save_index(self):
        """保存索引文件"""
        index_path = os.path.join(BASE_DIR, INDEX_FILE)
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(self.index_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存索引失败: {e}")
    
    def update_crop_region(self, filename, crop_region, cache_filename=None):
        """更新裁剪区域"""
        if filename in self.index_data["wallpapers"]:
            self.index_data["wallpapers"][filename]["crop_region"] = crop_region
            if cache_filename:
                self.index_data["wallpapers"][filename]["cache_path"] = cache_filename
            self.save_index()
    
    def get_wallpaper_list(self):
        """获取壁纸列表"""
        return list(self.index_data["wallpapers"].keys())

class IndexBuilder:
    """索引构建器 - 分离UI和逻辑"""
    def __init__(self, manager, parent_window=None):
        self.manager = manager
        self.parent_window = parent_window
        self.progress_window = None
        self.progress_label = None
        
    def build_with_ui(self):
        """带UI的构建"""
        if self.parent_window:
            self._create_progress_window()
        
        try:
            success = self.manager.build_index(self._progress_callback)
            return success
        finally:
            if self.progress_window:
                self.progress_window.destroy()
    
    def build_without_ui(self):
        """无UI的构建"""
        return self.manager.build_index(self._console_progress_callback)
    
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
    
    def _console_progress_callback(self, current, total, filename):
        """控制台进度回调"""
        print(f"处理中: {current+1}/{total} - {filename}")

class CropCanvas(Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.crop_region = None
        
        self.bind("<Button-1>", self.start_crop)
        self.bind("<B1-Motion>", self.update_crop)
        self.bind("<ButtonRelease-1>", self.end_crop)
    
    def start_crop(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect_id:
            self.delete(self.rect_id)
    
    def update_crop(self, event):
        if self.rect_id:
            self.delete(self.rect_id)
        self.rect_id = self.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="red", width=2
        )
    
    def end_crop(self, event):
        if self.start_x and self.start_y:
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            self.crop_region = (x1, y1, x2 - x1, y2 - y1)

class WallpaperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("壁纸预览与管理")
        self.manager = WallpaperManager()
        self.current_index = 0
        self.wallpaper_list = []
        self.excluded_files = set()
        self.random_seed = random.randint(1, 1000000)
        
        # 壁纸设置线程
        self.wallpaper_setter_thread = None
        self.wallpaper_setter_event = threading.Event()
        
        self.create_ui()
        self.initialize_data()
    
    def create_ui(self):
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
        self.excluded_files = get_excluded()
        
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
        builder = IndexBuilder(self.manager, self.root)
        success = builder.build_with_ui()
        if not success:
            messagebox.showerror("错误", "构建索引失败!")
    
    def need_rebuild_index(self):
        """检查是否需要重建索引"""
        if not os.path.exists(WALLPAPER_DIR):
            return False
        
        current_mtime = os.path.getmtime(WALLPAPER_DIR)
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
        """异步设置当前壁纸（优先使用缓存）"""
        if not self.wallpaper_list:
            return

        # 取消上一次的壁纸设置
        if self.wallpaper_setter_thread and self.wallpaper_setter_thread.is_alive():
            self.wallpaper_setter_event.set()
            self.wallpaper_setter_thread.join(timeout=0.1)
        self.wallpaper_setter_event.clear()

        filename = self.wallpaper_list[self.current_index]
        wallpaper_info = self.manager.index_data["wallpapers"][filename]

        # 优先使用缓存文件
        if wallpaper_info.get("cache_path") and wallpaper_info["cache_path"]:
            cache_path = os.path.join(BASE_DIR, CACHE_DIR, wallpaper_info["cache_path"])
            if os.path.exists(cache_path):
                path_to_set = cache_path
            else:
                path_to_set = wallpaper_info["path"]
        else:
            path_to_set = wallpaper_info["path"]

        # 启动异步线程延迟设置壁纸
        def setter(path, cancel_event):
            time.sleep(0.5)  # 延迟响应
            if not cancel_event.is_set():
                set_wallpaper(path)

        self.wallpaper_setter_thread = threading.Thread(
            target=setter, args=(path_to_set, self.wallpaper_setter_event), daemon=True
        )
        self.wallpaper_setter_thread.start()
    
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
            cache_path = os.path.join(BASE_DIR, CACHE_DIR, cache_filename)
            cropped.save(cache_path)

            # 获取屏幕分辨率
            screen_width, screen_height = get_screen_size()

            # 调整图片适配屏幕
            final_cache_path = os.path.join(BASE_DIR, CACHE_DIR, f"fit_{name}{ext}")
            fit_image_to_screen(cache_path, final_cache_path, screen_width, screen_height)

            # 更新索引
            self.manager.update_crop_region(filename, [crop_x, crop_y, crop_w, crop_h], os.path.basename(final_cache_path))
            
            # 设置为壁纸
            set_wallpaper(final_cache_path)
            
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
            add_to_excluded(filename)
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

def fit_image_to_screen(image_path, cache_path, screen_width, screen_height):
    """将图片缩放或超分辨率处理到适合屏幕大小，结果保存到cache_path"""
    img = Image.open(image_path)
    iw, ih = img.size

    # 判断是否需要缩小
    if iw > 2 * screen_width or ih > 2 * screen_height:
        scale = min(screen_width / iw, screen_height / ih)
        new_size = (int(iw * scale), int(ih * scale))
        img = img.resize(new_size, Image.LANCZOS)
        img.save(cache_path)
        return cache_path

    width_ratio = screen_width / iw
    height_ratio = screen_height / ih
    # 判断是否需要放大
    if width_ratio > 1 or height_ratio > 1:
        # 使用realesrgan放大
        realesrgan_path = os.path.join(BASE_DIR, "tools", "realesrgan", "realesrgan-ncnn-vulkan.exe")
        if os.path.exists(realesrgan_path):
            # 输出临时文件
            upscale_out = cache_path
            # 直到大于等于屏幕尺寸
            scale = int(max(width_ratio, height_ratio))
            
            if scale < 2:
                scale = 2
            elif scale > 8:
                scale = 8

            tmp_in = image_path
            while True:
                cmd = [
                    realesrgan_path,
                    "-i", tmp_in,
                    "-o", upscale_out,
                    "-s", str(scale)
                ]
                subprocess.run(cmd, check=True)
                up_img = Image.open(upscale_out)
                if up_img.width >= screen_width or up_img.height >= screen_height:
                    break
                tmp_in = upscale_out
            return upscale_out
        else:
            # 未找到realesrgan，直接返回原图
            img.save(cache_path)
            return cache_path

    # 不需要处理，直接保存副本
    img.save(cache_path)
    return cache_path

if __name__ == '__main__':
    use_gui = True  # 修复这个变量位置
    
    if use_gui:
        root = tk.Tk()
        root.geometry("800x600")
        app = WallpaperApp(root)
        root.mainloop()
    else:
        # 命令行模式
        print("命令行模式")
        manager = WallpaperManager()
        builder = IndexBuilder(manager)
        
        if not manager.load_index() or input("是否重建索引? (y/n): ").lower() == 'y':
            builder.build_without_ui()
        
        # 命令行逻辑...
        while True:
            command = input("输入命令 (next/prev/crop/exclude/exit): ").strip().lower()
            if command == 'next':
                manager.next_wallpaper()
            elif command == 'prev':
                manager.prev_wallpaper()
            elif command == 'crop':
                # 处理裁剪逻辑
                pass
            elif command == 'exclude':
                # 处理排除逻辑
                pass
            elif command == 'exit':
                break
            else:
                print("未知命令，请重试。")
