import sys

import requests
from pathlib import Path
from ctypes import windll
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Union

from src.Downloader import Downloader
from src.utils.DataUnit import DownloadPackage
from src.Crawler import VideoCrawler
from src.Config.Config import config


video_crawler = VideoCrawler()
STANDARD_IMAGE_SIZE = (800, 538)
STANDARD_IMAGE_SIZE_WIDTH = STANDARD_IMAGE_SIZE[0]

_download_dir = {}

windll.shcore.SetProcessDpiAwareness(1)
root = tk.Tk()
scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100
root.tk.call('tk', 'scaling', scale_factor)
root.title("视频下载器")
root.resizable(False, False)

window_width = root.winfo_screenwidth()
window_height = root.winfo_screenheight()
print(window_width, window_height)

root.geometry(f'800x600+{window_width//2-400}+{window_height//2-300}')
print(root.geometry())

root.columnconfigure(0, weight=1)
root.columnconfigure(3, weight=1)

root.rowconfigure(2, weight=1)

title_label = tk.Label(root, text="视频下载器", font=("Arial", 24))
title_label.grid(row=0, column=0, columnspan=4, sticky=tk.W + tk.E, pady=20)


def start_download() -> None:
    id = entry.get()
    src = source_combobox.get()
    if not id:
        messagebox.showerror("错误", "请输入视频链接或ID")
    try:
        crawler = video_crawler._avaliable_crawlers[src]()
        crawler.path = crawler.path_to_video
        crawler.parameters = f'{id}/'
        crawler.url = crawler._construct_url()
        print(crawler.url)
        download_package = crawler.parse()
        _download_dir[id] = download_package
    except Exception as e:
        messagebox.showerror("错误", f"下载失败: {e}")

def video_page(
        download_package : DownloadPackage
        ) -> None:
    cover_url = download_package.cover_url
    response = requests.get(cover_url, headers=config.headers, proxies=config.proxies, timeout=10)
    if response.status_code == 200:
        with open(config.cover_dir / f'{download_package.id.lower()}.jpg', 'wb') as f:
            f.write(response.content)
        image_path = config.cover_dir / f'{download_package.id.lower()}.jpg'
    else:
        image_path = config.assets_dir / 'cover.jpg'
    image = Image.open(image_path)
    cover_window = tk.Toplevel(root)
    cover_window.resizable(False, False)
    cover_window.title("视频详情页")
    cover_window.geometry(f'800x600+{window_width//2-400}+{window_height//2-300}')
    
    cover = resize_image(image, 3)

    image_frame = tk.Frame(cover_window, relief=tk.RIDGE, borderwidth=1)
    image_frame.pack(side=tk.LEFT)

    label_image = tk.Label(image_frame, image=cover, relief=tk.RIDGE, borderwidth=1)
    label_image.pack(side=tk.TOP, pady=(100, 50),padx=20)
    cover_window.image = cover

    name = download_package.name
    if name:
        name_length = len(name)
        if name_length > 30:
            name = name[:30] + "..."
        else:
            name = name
    else:
        name = "测试视频"

    tags = ' '.join(download_package.hash_tags if download_package.hash_tags else [])
    if tags:
        tag_length = len(tags)
        if tag_length > 30:
            tags = tags[:30] + "..."
        else:
            tags = tags
    else:
        tags = "无"

    button_frame = tk.Frame(image_frame, relief=tk.RIDGE, borderwidth=1)
    button_frame.pack(side=tk.TOP, pady=70)

    add_to_list_button = tk.Button(button_frame, text="添加到下载列表", command=lambda: add_to_lst(image=image, package=download_package))
    add_to_list_button.grid(row=0, column=0, padx=(0, 50), pady=20)

    download_button = tk.Button(button_frame, text="开始下载", command=lambda: add_and_download(image=image, package=download_package))
    download_button.grid(row=0, column=1, padx=10, pady=20)

    video_info_frame = tk.Frame(cover_window, relief=tk.RIDGE, borderwidth=1)
    video_info_frame.pack(side=tk.LEFT, fill='x', expand=True)

    for i in range(3):
        video_info_frame.columnconfigure(i, weight=1, uniform='group1')

    title_label = tk.Label(video_info_frame, text="视频信息", font=("Segoe UI Variable", 18),
                           relief=tk.RIDGE, borderwidth=1, anchor='center')
    title_label.grid(row=0, column=0, columnspan=3, sticky='ew', pady=20)

    def add_info_row(
            row, 
            label_text, 
            value_text, 
            value_font_size=14, 
            value_width=20,
            value_height=2, 
            textvariable : tk.Variable| None = None
            ) -> tk.Label:
        left_label = tk.Label(video_info_frame, text=label_text, font=("Segoe UI Variable", 14),
                              relief=tk.RIDGE, borderwidth=1, anchor='center', width=8, height=value_height)
        left_label.grid(row=row, column=0, sticky='ew', pady=10, padx=2)

        if textvariable:
            right_label = tk.Label(video_info_frame, font=("Segoe UI Variable", value_font_size),
                                relief=tk.RIDGE, borderwidth=1, anchor='center', width=value_width, textvariable=textvariable, height=value_height)
        else:
            right_label = tk.Label(video_info_frame, text=value_text, font=("Segoe UI Variable", value_font_size),
                    relief=tk.RIDGE, borderwidth=1, anchor='center', width=value_width, height=value_height)
        right_label.grid(row=row, column=1, columnspan=2, sticky='ew', pady=10, padx=2)
        return right_label

    id_text = add_info_row(1, "番    号：", f"{download_package.id}", value_width=25)
    name_text = add_info_row(2, "名    称：", f"{name}", value_font_size=10, value_width=30)
    actor_text = add_info_row(3, "演    员：", f"{download_package.actress}", value_width=25)
    tag_text = add_info_row(4, "标    签：", f"{tags}", value_width=25)
    release_date_text = add_info_row(5, "上映日期：", f"{download_package.release_date}", value_width=25)
    duration_text = add_info_row(6, "时    长：", f"{download_package.time_length}", value_width=25)

    name_text.config(wraplength=200)
    tag_text.config(wraplength=200)

def resize_image(image : Image.Image, scale_factor : Union[int, float] = 1) -> ImageTk.PhotoImage:
    width, height = image.size
    new_width = int(width // scale_factor)
    new_height = int(height // scale_factor)
    image = image.resize((new_width, new_height))
    return ImageTk.PhotoImage(image)

label = tk.Label(root, text="请输入番号:")
label.grid(row=1, column=0)


entry = tk.Entry(root, width=30)
entry.grid(row=1, column=1)

crawler_src = video_crawler.avaliable_sources

source_combobox = ttk.Combobox(root, state="readonly", values=crawler_src)
source_combobox.current(0)
source_combobox.grid(row=1, column=2)

button = tk.Button(root, text="开始下载", command=start_download)
button.grid(row=1, column=3)

clear_button = tk.Button(root, text="清空", command=lambda: video_page(_download_dir.get(entry.get(), DownloadPackage())))
clear_button.grid(row=1, column=4, padx=10)

notebook = ttk.Notebook(root, name='下载列表')
notebook.grid(row=2, column=0, columnspan=4, sticky='nsew')

download_list_frame = tk.Frame(notebook, name='download_list_frame')
notebook.add(download_list_frame, text='下载列表')

log_frame = tk.Frame(notebook, name='log_frame')
notebook.add(log_frame, text='日志')

download_list_canvas = tk.Canvas(download_list_frame, borderwidth=0, highlightthickness=0)
download_list_scrollbar = tk.Scrollbar(download_list_frame, orient=tk.VERTICAL, command=download_list_canvas.yview)
download_list_scrollable_frame = tk.Frame(download_list_canvas, borderwidth=0)

download_list_scrollable_frame.bind(
    "<Configure>",
    lambda e: download_list_canvas.configure(scrollregion=download_list_canvas.bbox("all"))
)

download_list_canvas.create_window((0, 0), window=download_list_scrollable_frame, anchor="nw")
download_list_canvas.configure(yscrollcommand=download_list_scrollbar.set)

download_list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
download_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def _on_mousewheel(event):
    x, y = root.winfo_pointerxy()
    widget_under_mouse = root.winfo_containing(x, y)
    while widget_under_mouse:
        if widget_under_mouse == download_list_canvas:
            download_list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            return "break"
        widget_under_mouse = widget_under_mouse.master
    return None

root.bind_all("<MouseWheel>", _on_mousewheel, add=True)

def add_to_lst(
        image : Image.Image,
        package : DownloadPackage,
        ):
    demo_image = resize_image(image=image, scale_factor=4)
    
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

def add_and_download(
        image : Image.Image,
        package : DownloadPackage
        ) -> None:
    add_to_lst(image=image, package=package)
    downloader = Downloader(package)
    downloader.download()


log_text = tk.Text(log_frame, wrap=tk.WORD)
log_scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
log_text.configure(yscrollcommand=log_scrollbar.set)

log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_text.insert(tk.END, "日志信息示例\n" * 50)

root.mainloop()