import tkinter as tk

class CropCanvas(tk.Canvas):
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