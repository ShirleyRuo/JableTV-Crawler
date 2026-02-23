from __future__ import annotations

from ctypes import windll
import tkinter as tk
from pathlib import Path
import queue
from threading import Thread
from dataclasses import dataclass, field
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from typing import Union, Tuple, Dict, List

from src.utils.DataUnit import DownloadPackage
from src.Crawler import VideoCrawler

STANDARD_IMAGE_SIZE = (800, 538)
STANDARD_IMAGE_SIZE_WIDTH = STANDARD_IMAGE_SIZE[0]
STANDARD_IMAGE_SIZE_HEIGHT = STANDARD_IMAGE_SIZE[1]
STANDARD_WINDOW_SIZE = (800, 600)

VIDEO_CRAWLER = VideoCrawler()

def get_crawler_src() -> List[str]:
    return VIDEO_CRAWLER.avaliable_sources

def get_download_dict() -> Dict[str, DownloadPackage]:
    return {}

image = Image.open(r"D:\桌面\Video\downloads\cover\kam-272.jpg")
download_package = DownloadPackage(id = '123456')

@dataclass
class AppData:
    download_dict : Dict[str, DownloadPackage] = field(default_factory=get_download_dict)
    crawler_src : List[str] = field(default_factory=get_crawler_src)

class VideoPage(ttk.Frame):

    def __init__(
            self, 
            parent : ttk.Frame, 
            controller : VideoCrawlerApp,
            app_data : AppData,
            **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.app_data = app_data
        self.download_package = DownloadPackage()

        image_frame = tk.Frame(self, relief=tk.RIDGE, borderwidth=1)
        image_frame.pack(side=tk.LEFT)

        image_obj = self.controller.resize_image(image=image, scale_factor=3)
        label_image = tk.Label(image_frame, image=image_obj, relief=tk.RIDGE, borderwidth=1)
        label_image.pack(side=tk.TOP, pady=(100, 50),padx=20)
        self.image = image_obj

        name = self._set_text(download_package.name, "测试视频")

        tags = ' '.join(download_package.hash_tags if download_package.hash_tags else [])
        tags = self._set_text(tags, "无")

        button_frame = tk.Frame(image_frame, relief=tk.RIDGE, borderwidth=1)
        button_frame.pack(side=tk.TOP, pady=70)

        add_to_list_button = tk.Button(button_frame, text="添加到下载列表", command=lambda: self.controller.add_to_lst(image=image, package=download_package))
        add_to_list_button.grid(row=0, column=0, padx=(0, 50), pady=20)

        download_button = tk.Button(button_frame, text="开始下载")
        download_button.grid(row=0, column=1, padx=10, pady=20)

        return_button = tk.Button(button_frame, text="返回", command=lambda: self.controller.show_page("CrawlerFrame"))
        return_button.grid(row=0, column=2, padx=(50, 0), pady=20)

        video_info_frame = tk.Frame(self, relief=tk.RIDGE, borderwidth=1)
        video_info_frame.pack(side=tk.LEFT, fill='x', expand=True)

        for i in range(3):
            video_info_frame.columnconfigure(i, weight=1, uniform='group1')

        title_label = tk.Label(video_info_frame, text="视频信息", font=("Segoe UI Variable", 18),
                            relief=tk.RIDGE, borderwidth=1, anchor='center')
        title_label.grid(row=0, column=0, columnspan=3, sticky='ew', pady=20)

        id_text = self.add_info_row(video_info_frame, 1, "番    号：", f"{download_package.id}", value_width=25)
        name_text = self.add_info_row(video_info_frame, 2, "名    称：", f"{name}", value_font_size=10, value_width=30)
        actor_text = self.add_info_row(video_info_frame, 3, "演    员：", f"{download_package.actress}", value_width=25)
        tag_text = self.add_info_row(video_info_frame, 4, "标    签：", f"{tags}", value_width=25)
        release_date_text = self.add_info_row(video_info_frame, 5, "上映日期：", f"{download_package.release_date}", value_width=25)
        duration_text = self.add_info_row(video_info_frame, 6, "时    长：", f"{download_package.time_length}", value_width=25)

        name_text.config(wraplength=200)
        tag_text.config(wraplength=200)

    def add_info_row(
            self,
            master : ttk.Frame | tk.Frame,
            row, 
            label_text, 
            value_text, 
            value_font_size=14, 
            value_width=20,
            value_height=2, 
            textvariable : tk.Variable| None = None
            ) -> tk.Label:
        left_label = tk.Label(master=master, text=label_text, font=("Segoe UI Variable", 14),
                            relief=tk.RIDGE, borderwidth=1, anchor='center', width=8, height=value_height)
        left_label.grid(row=row, column=0, sticky='ew', pady=10, padx=2)

        if textvariable:
            right_label = tk.Label(master=master, font=("Segoe UI Variable", value_font_size),
                                relief=tk.RIDGE, borderwidth=1, anchor='center', width=value_width, textvariable=textvariable, height=value_height)
        else:
            right_label = tk.Label(master=master, text=value_text, font=("Segoe UI Variable", value_font_size),
                    relief=tk.RIDGE, borderwidth=1, anchor='center', width=value_width, height=value_height)
        right_label.grid(row=row, column=1, columnspan=2, sticky='ew', pady=10, padx=2)
        return right_label
    
    def _set_text(self, text : str, default_text : str = "无") -> str:
        if text:
            text_length = len(text)
            if text_length > 30:
                text = text[:30] + "..."
            else:
                text = text
        else:
            text = default_text
        return text

    def start_download(self) -> None:
        self.controller.add_to_lst(image=image, package=download_package)
        self.controller.show_page('CrawlerFrame')
        self.ensure_win.destroy()
    
    def ensure_win_widget(self) -> None:
        self.ensure_win = tk.Toplevel(self)
        self.ensure_win.title("确认")
        self.controller._center_window(self.ensure_win,300, 100, self.controller)
        self.ensure_win.resizable(False, False)

        self.ensure_win_label = tk.Label(self.ensure_win, text="是否要下载该视频？")
        self.ensure_win_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.ensure_win_yes_button = tk.Button(self.ensure_win, text="是", command=self.start_download)
        self.ensure_win_yes_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.ensure_win_no_button = tk.Button(self.ensure_win, text="否", command=lambda: self.ensure_win.destroy())
        self.ensure_win_no_button.pack(side=tk.RIGHT, fill=tk.X, expand=True)

class CrawlerFrame(ttk.Frame):

    def __init__(
            self, 
            parent : ttk.Frame, 
            controller : VideoCrawlerApp,
            app_data : AppData,
            **kwargs
            ) -> None:
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.app_data = app_data
        self.video_page_dict : Dict[str, VideoPage] = {}
        self.columnconfigure(0, weight=1)
        self.columnconfigure(3, weight=1)

        self.rowconfigure(2, weight=1)

        self.title_label = tk.Label(self, text="视频下载器", font=("Arial", 24))
        self.title_label.grid(row=0, column=0, columnspan=4, sticky=tk.W + tk.E, pady=20)

        self.label = tk.Label(self, text="请输入番号:")
        self.label.grid(row=1, column=0)
        self.entry = tk.Entry(self, width=30)
        self.entry.grid(row=1, column=1)

        crawler_src = self.app_data.crawler_src

        self.source_combobox = ttk.Combobox(self, state="readonly", values=crawler_src)
        self.source_combobox.current(0)
        self.source_combobox.grid(row=1, column=2)

        self.button = tk.Button(self, text="开始下载", command=self.search_video)
        self.button.grid(row=1, column=3)

        self.clear_button = tk.Button(self, text="清空", command=lambda: self.entry.delete(0, tk.END))
        self.clear_button.grid(row=1, column=4, padx=10)

        self.notebook = ttk.Notebook(self, name='下载列表')
        self.notebook.grid(row=2, column=0, columnspan=4, sticky='nsew')

        self.download_list_frame = tk.Frame(self.notebook, name='download_list_frame')
        self.notebook.add(self.download_list_frame, text='下载列表')

        self.log_frame = tk.Frame(self.notebook, name='log_frame')
        self.notebook.add(self.log_frame, text='日志')

        self.download_list_canvas = tk.Canvas(self.download_list_frame, borderwidth=0, highlightthickness=0)
        self.download_list_scrollbar = tk.Scrollbar(self.download_list_frame, orient=tk.VERTICAL, command=self.download_list_canvas.yview)
        self.download_list_scrollable_frame = tk.Frame(self.download_list_canvas, borderwidth=0)

        self.download_list_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.download_list_canvas.configure(scrollregion=self.download_list_canvas.bbox("all"))
        )

        self.download_list_canvas.create_window((0, 0), window=self.download_list_scrollable_frame, anchor="nw")
        self.download_list_canvas.configure(yscrollcommand=self.download_list_scrollbar.set)

        self.download_list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.download_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.bind_all("<MouseWheel>", self._on_mousewheel, add=True)
    
    def search_video(self) -> None:
        self.button.config(state=tk.DISABLED)
        search_thread = Thread(target=self.search)
        search_thread.start()
        self.controller.show_page('VideoPage')
    
    def search(self) -> None:
        import time
        time.sleep(15)

    def _on_mousewheel(self,event):
        x, y = self.winfo_pointerxy()
        widget_under_mouse = self.winfo_containing(x, y)
        while widget_under_mouse:
            if widget_under_mouse == self.download_list_canvas:
                self.download_list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
            widget_under_mouse = widget_under_mouse.master
        return None


class VideoCrawlerApp(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.title("视频下载器")
        self.resizable(False, False)
        self._frames : Dict[str, ttk.Frame] = {}
        self._data : AppData = AppData()
        self._current_frame : ttk.Frame | None = None
        self.queue = queue.Queue()
        self._set_high_resolution_dpi()

        self._set_window()

        container = ttk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for F in (CrawlerFrame, VideoPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self, app_data=self._data)
            self._frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_page("CrawlerFrame")
        self.after(100, self._check_queue)
    
    def _check_queue(self) -> None:
        pass
    
    def _center_window(
            self,
            win : tk.Toplevel,
            win_width : int, 
            win_height : int,
            root : Union[tk.Tk, ttk.Frame]
            ) -> None:
        root_win_width = root.winfo_width()
        root_win_height = root.winfo_height()
        win_x = root.winfo_rootx() + (root_win_width - win_width) // 2
        win_y = root.winfo_rooty() + (root_win_height - win_height) // 2
        win.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")

    def _set_high_resolution_dpi(self) -> None:
        windll.shcore.SetProcessDpiAwareness(1)
        scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100
        self.tk.call('tk', 'scaling', scale_factor)
    
    def _get_window_size(self) -> Tuple[int, int]:
        window_width = self.winfo_screenwidth()
        window_height = self.winfo_screenheight()
        return window_width, window_height
    
    def _set_window(self) -> None:
        window_width, window_height = self._get_window_size()
        self.geometry(
            f'{int(STANDARD_WINDOW_SIZE[0])}x{int(STANDARD_WINDOW_SIZE[1])}+{int(window_width//2 - STANDARD_WINDOW_SIZE[0]/2)}+{int(window_height//2 - STANDARD_WINDOW_SIZE[1]/2)}'
            )
    
    def show_page(self, page_name : str) -> None:
        frame = self._frames.get(page_name)
        if frame:
            frame.tkraise()
            self._current_frame = frame
    
    def messagebox_info(
            self,
            master : tk.Tk | ttk.Frame,
            title : str, 
            message : str
            ) -> None:
        messagebox_win = tk.Toplevel(master=master)
        messagebox_win.title(title)
        messagebox_win.resizable(False, False)
        self._center_window(win=messagebox_win,win_width=300,win_height=100, root=master)

        text_label = tk.Label(messagebox_win, text=message)
        text_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        ok_button = tk.Button(messagebox_win, text="确定", command=lambda: messagebox_win.destroy())
        ok_button.pack(side=tk.BOTTOM, fill=tk.X, expand=True)

    def add_to_lst(
            self,
            image : Image.Image,
            package : DownloadPackage,
            ) -> None:
        if package.id:
            if package.id in self._data.download_dict:
                if self._current_frame:
                    self.messagebox_info(master=self._current_frame, title="错误", message="该视频已存在下载列表中。")
                    return
            self._data.download_dict[package.id] = package
        else:
            raise ValueError("DownloadPackage id不能为空.")
        demo_image = self.resize_image(image=image, scale_factor=4)
        
        crawler_frame = self._frames.get('CrawlerFrame')
        if crawler_frame and isinstance(crawler_frame, CrawlerFrame):
            download_list_scrollable_frame = crawler_frame.download_list_scrollable_frame
        
        item_frame = tk.Frame(download_list_scrollable_frame, relief=tk.RIDGE, borderwidth=1)
        item_frame.pack(fill=tk.X, padx=5, pady=5)
        
        img_label = tk.Label(item_frame, image=demo_image)
        img_label.image = demo_image
        img_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        info_frame = tk.Frame(item_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        info_data = [
            ("番号:", package.id),
            ("名称:", package.name),
            ("演员:", package.actress),
            ("标签:", ' '.join(package.hash_tags if package.hash_tags else ())),
            ("上映日期:", package.release_date),
            ("时长:", package.time_length)
        ]
        
        for i, (label, value) in enumerate(info_data):
            row_frame = tk.Frame(info_frame)
            row_frame.pack(fill=tk.X, pady=2)
            lbl = tk.Label(row_frame, text=label, width=8, anchor='e')
            lbl.pack(side=tk.LEFT)
            val = tk.Label(row_frame, text=value, anchor='w', wraplength=300)
            val.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if self._current_frame:
            self.messagebox_info(master=self._current_frame, title="成功", message="视频已添加到下载列表。")
    
    @staticmethod
    def load_image(path : Union[str, Path]) -> Image.Image:
        return Image.open(path)

    @staticmethod
    def resize_image(
            image : Image.Image, 
            scale_factor : Union[int, float] = 1
            ) -> ImageTk.PhotoImage:
        width, height = image.size
        new_width = int(width // scale_factor)
        new_height = int(height // scale_factor)
        image = image.resize((new_width, new_height))
        return ImageTk.PhotoImage(image) 
    
    def run(self) -> None:
        self.mainloop()