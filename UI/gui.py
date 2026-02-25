from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
import requests
from threading import Thread
from dataclasses import dataclass, field
from PIL import Image, ImageTk
from typing import Union, Tuple, Dict, List
from ctypes import windll

from src.utils.DataUnit import DownloadPackage
from src.utils.Logger import set_logger_queue
from src.Crawler import VideoCrawler
from src.Downloader import Downloader
from src.Config.Config import config

STANDARD_IMAGE_SIZE = (800, 538)
STANDARD_WINDOW_SIZE = (800, 600)

default_image = Image.open(r'D:\桌面\Video\assets\cover.jpg')
VIDEO_CRAWLER = VideoCrawler()

def get_crawler_src() -> List[str]:
    return VIDEO_CRAWLER.avaliable_sources

def get_download_dict() -> Dict[str, DownloadPackage]:
    return {}

sample_package = DownloadPackage(
    id='ABC-123',
    name='示例视频标题可能很长所以需要截断显示',
    actress='示例演员',
    hash_tags=['标签1', '标签2', '标签3'],
    release_date='2025-01-01',
    time_length='120分钟'
)

@dataclass
class AppData:
    download_dict: Dict[str, DownloadPackage] = field(default_factory=get_download_dict)
    crawler_src: List[str] = field(default_factory=get_crawler_src)


class VideoPage(ttk.Frame):
    def __init__(self, parent: ttk.Frame, controller: VideoCrawlerApp, app_data: AppData, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.app_data = app_data
        self.download_package = DownloadPackage()
        self.current_image = default_image.copy()

        self.image_label = None
        self.id_label = None
        self.name_label = None
        self.actor_label = None
        self.tag_label = None
        self.release_label = None
        self.duration_label = None

        self._create_widgets()
        self.update_data(sample_package, default_image)

    def _create_widgets(self):
        image_frame = tk.Frame(self, relief=tk.RIDGE, borderwidth=1)
        image_frame.pack(side=tk.LEFT)

        self.image_label = tk.Label(image_frame, relief=tk.RIDGE, borderwidth=1)
        self.image_label.pack(side=tk.TOP, pady=(100, 50), padx=20)

        button_frame = tk.Frame(image_frame, relief=tk.RIDGE, borderwidth=1)
        button_frame.pack(side=tk.TOP, pady=70)

        add_to_list_button = tk.Button(button_frame, text="添加到下载列表",command=self._add_to_list)
        add_to_list_button.grid(row=0, column=0, padx=(0, 50), pady=20)

        download_button = tk.Button(button_frame, text="开始下载", command=self.download)
        download_button.grid(row=0, column=1, padx=10, pady=20)

        return_button = tk.Button(button_frame, text="返回",
                                   command=lambda: self.controller.show_page("CrawlerFrame"))
        return_button.grid(row=0, column=2, padx=(50, 0), pady=20)

        video_info_frame = tk.Frame(self, relief=tk.RIDGE, borderwidth=1)
        video_info_frame.pack(side=tk.LEFT, fill='x', expand=True)
        for i in range(3):
            video_info_frame.columnconfigure(i, weight=1, uniform='group1')

        title_label = tk.Label(video_info_frame, text="视频信息", font=("Segoe UI Variable", 18),
                               relief=tk.RIDGE, borderwidth=1, anchor='center')
        title_label.grid(row=0, column=0, columnspan=3, sticky='ew', pady=20)

        self.id_label = self.add_info_row(video_info_frame, 1, "番    号：", "", value_width=25)
        self.name_label = self.add_info_row(video_info_frame, 2, "名    称：", "", value_font_size=10, value_width=30)
        self.actor_label = self.add_info_row(video_info_frame, 3, "演    员：", "", value_width=25)
        self.tag_label = self.add_info_row(video_info_frame, 4, "标    签：", "", value_width=25)
        self.release_label = self.add_info_row(video_info_frame, 5, "上映日期：", "", value_width=25)
        self.duration_label = self.add_info_row(video_info_frame, 6, "时    长：", "", value_width=25)

        self.name_label.config(wraplength=200)
        self.tag_label.config(wraplength=200)

    def add_info_row(self, master, row, label_text, value_text, value_font_size=14,
                     value_width=20, value_height=2, textvariable=None):
        left_label = tk.Label(master, text=label_text, font=("Segoe UI Variable", 14),
                              relief=tk.RIDGE, borderwidth=1, anchor='center', width=8, height=value_height)
        left_label.grid(row=row, column=0, sticky='ew', pady=10, padx=2)

        if textvariable:
            right_label = tk.Label(master, font=("Segoe UI Variable", value_font_size),
                                   relief=tk.RIDGE, borderwidth=1, anchor='center',
                                   width=value_width, textvariable=textvariable, height=value_height)
        else:
            right_label = tk.Label(master, text=value_text, font=("Segoe UI Variable", value_font_size),
                                   relief=tk.RIDGE, borderwidth=1, anchor='center',
                                   width=value_width, height=value_height)
        right_label.grid(row=row, column=1, columnspan=2, sticky='ew', pady=10, padx=2)
        return right_label

    def update_data(self, package: DownloadPackage, image: Image.Image):
        self.download_package = package
        self.current_image = image

        photo = self.controller.resize_image(image, scale_factor=3)
        self.image_label.config(image=photo)
        self.image_label.image = photo

        def safe_text(text, default="无"):
            return text if text else default

        self.id_label.config(text=safe_text(package.id))
        self.name_label.config(text=self._set_text(package.name, "测试视频"))
        tags = ' '.join(package.hash_tags if package.hash_tags else [])
        self.tag_label.config(text=self._set_text(tags, "无"))
        self.actor_label.config(text=safe_text(package.actress))
        self.release_label.config(text=safe_text(package.release_date))
        self.duration_label.config(text=safe_text(package.time_length))
    
    def download(self) -> None:
        self.controller.show_page('CrawlerFrame')
        self.download_thread = Thread(target=self._download_video)
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def _download_video(self) -> None:
        if not self.controller._data.download_dict.get(self.download_package.id):
            self._add_to_list()
        if packages := list(self.controller._data.download_dict.values()):
            downloader = Downloader(packages=packages)
            downloader.download()
    
    def _set_text(self, text: str, default_text: str = "无") -> str:
        if text:
            text_length = len(text)
            if text_length > 30:
                text = text[:30] + "..."
        else:
            text = default_text
        return text

    def _add_to_list(self):
        self.controller.add_to_lst(image=self.current_image, package=self.download_package)

class CrawlerFrame(ttk.Frame):
    def __init__(self, parent: ttk.Frame, controller: VideoCrawlerApp, app_data: AppData, **kwargs):
        super().__init__(parent, **kwargs)
        self.controller = controller
        self.app_data = app_data
        self.video_page_dict = {}
        self.search_thread = None
        self.search_cancelled = False
        self.wait_win = None

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

        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.download_list_canvas = tk.Canvas(self.download_list_frame, borderwidth=0, highlightthickness=0)
        self.download_list_scrollbar = tk.Scrollbar(self.download_list_frame, orient=tk.VERTICAL,
                                                     command=self.download_list_canvas.yview)
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

    def search_video(self):
        self.button.config(state=tk.DISABLED)

        video_id = self.entry.get().strip()
        if not video_id:
            self.controller.messagebox_info(self, "提示", "请输入番号")
            self.button.config(state=tk.NORMAL)
            return
        source = self.source_combobox.get()

        self.wait_win = tk.Toplevel(self)
        self.wait_win.title("请稍候")
        self.wait_win.resizable(False, False)
        self.controller._center_window(self.wait_win, 300, 120, self)
        self.wait_win.transient(self)

        label = tk.Label(self.wait_win, text="正在搜索，请稍候...")
        label.pack(pady=20)

        cancel_btn = tk.Button(self.wait_win, text="取消", command=self.cancel_search)
        cancel_btn.pack(pady=5)

        self.search_cancelled = False
        self.search_thread = Thread(target=self._do_search, args=(video_id, source))
        self.search_thread.daemon = True
        self.search_thread.start()

    def _do_search(self, video_id: str, source: str):
        try:
            if self.search_cancelled:
                self.controller._search_queue.put(('cancelled', None))
                return
            crawler = VIDEO_CRAWLER._avaliable_crawlers[source]()
            crawler.path = crawler.path_to_video
            crawler.parameters = f'{video_id}/'
            crawler.url = crawler._construct_url()
            download_package = crawler.parse()          
            image = self._fetch_image(download_package)
            self.controller._search_queue.put(('success', (download_package, image)))
        except Exception as e:
            self.controller._search_queue.put(('error', str(e)))

    def cancel_search(self):
        self.search_cancelled = True
        if self.wait_win:
            self.wait_win.destroy()
            self.wait_win = None
        self.button.config(state=tk.NORMAL)

    def _on_mousewheel(self, event):
        x, y = self.winfo_pointerxy()
        widget_under_mouse = self.winfo_containing(x, y)
        while widget_under_mouse:
            if widget_under_mouse == self.download_list_canvas:
                self.download_list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                return "break"
            widget_under_mouse = widget_under_mouse.master
        return None

    def _fetch_image(self, package: DownloadPackage) -> Image.Image:
        cover_url = package.cover_url
        response = requests.get(cover_url, headers=config.headers, proxies=config.proxies, timeout=10)
        if response.status_code == 200:
            with open(config.cover_dir / f'{package.id.lower()}.jpg', 'wb') as f:
                f.write(response.content)
            image_path = config.cover_dir / f'{package.id.lower()}.jpg'
        else:
            image_path = config.assets_dir / 'cover.jpg'
        image = Image.open(image_path)
        return image

    def append_log(self, log_msg: str):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f'{log_msg}\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

class VideoCrawlerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("视频下载器")
        self.resizable(False, False)
        self._frames: Dict[str, ttk.Frame] = {}
        self._data: AppData = AppData()
        self._current_frame: ttk.Frame | None = None
        self._search_queue = queue.Queue()
        self._log_queue = queue.Queue()
        set_logger_queue(self._log_queue)
        self._download_queue = queue.Queue()

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

    def _set_high_resolution_dpi(self):
        try:
            windll.shcore.SetProcessDpiAwareness(1)
            scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100
            self.tk.call('tk', 'scaling', scale_factor)
        except Exception:
            pass

    def _check_queue(self):
        try:
            while True:
                msg, data =self._search_queue.get_nowait()
                if msg == 'success':
                    package, image = data
                    video_page : VideoPage = self._frames.get('VideoPage')
                    if video_page:
                        video_page.update_data(package, image)
                    crawler_frame : CrawlerFrame = self._frames.get('CrawlerFrame')
                    if crawler_frame and crawler_frame.wait_win:
                        crawler_frame.wait_win.destroy()
                        crawler_frame.wait_win = None
                    crawler_frame.button.config(state=tk.NORMAL)
                    self.show_page('VideoPage')
                elif msg == 'error':
                    error_msg = data
                    self.messagebox_info(self, "错误", f"搜索失败：{error_msg}")
                    crawler_frame = self._frames.get('CrawlerFrame')
                    if crawler_frame:
                        if crawler_frame.wait_win:
                            crawler_frame.wait_win.destroy()
                            crawler_frame.wait_win = None
                        crawler_frame.button.config(state=tk.NORMAL)
                elif msg == 'cancelled':
                    crawler_frame = self._frames.get('CrawlerFrame')
                    if crawler_frame:
                        crawler_frame.button.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        try:
            while True:
                msg, log_msg = self._log_queue.get_nowait()
                if msg == 'log':
                    crawler_frame : CrawlerFrame = self._frames.get('CrawlerFrame')
                    if crawler_frame:
                        crawler_frame.append_log(log_msg)
        except queue.Empty:
            pass
        # try:
        #     while True:
        #         download_package = self._download_queue.get_nowait()
        # except queue.Empty:
        #     pass
        self.after(100, self._check_queue)

    def _center_window(self, win: tk.Toplevel, win_width: int, win_height: int, root: Union[tk.Tk, ttk.Frame]):
        root_win_width = root.winfo_width()
        root_win_height = root.winfo_height()
        win_x = root.winfo_rootx() + (root_win_width - win_width) // 2
        win_y = root.winfo_rooty() + (root_win_height - win_height) // 2
        win.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")

    def _get_window_size(self) -> Tuple[int, int]:
        window_width = self.winfo_screenwidth()
        window_height = self.winfo_screenheight()
        return window_width, window_height

    def _set_window(self):
        window_width, window_height = self._get_window_size()
        self.geometry(
            f'{int(STANDARD_WINDOW_SIZE[0])}x{int(STANDARD_WINDOW_SIZE[1])}+{int(window_width//2 - STANDARD_WINDOW_SIZE[0]/2)}+{int(window_height//2 - STANDARD_WINDOW_SIZE[1]/2)}'
        )

    def show_page(self, page_name: str):
        frame = self._frames.get(page_name)
        if frame:
            frame.tkraise()
            self._current_frame = frame

    def messagebox_info(self, master: tk.Tk | ttk.Frame, title: str, message: str):
        messagebox_win = tk.Toplevel(master=master)
        messagebox_win.title(title)
        messagebox_win.resizable(False, False)
        self._center_window(win=messagebox_win, win_width=300, win_height=100, root=master)

        text_label = tk.Label(messagebox_win, text=message)
        text_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        ok_button = tk.Button(messagebox_win, text="确定", command=lambda: messagebox_win.destroy())
        ok_button.pack(side=tk.BOTTOM, fill=tk.X, expand=True)

    def add_to_lst(self, image: Image.Image, package: DownloadPackage):
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
        else:
            return

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
    def resize_image(image: Image.Image, scale_factor: Union[int, float] = 1) -> ImageTk.PhotoImage:
        width, height = image.size
        new_width = int(width // scale_factor)
        new_height = int(height // scale_factor)
        image = image.resize((new_width, new_height))
        return ImageTk.PhotoImage(image)
    
    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = VideoCrawlerApp()
    app.run()