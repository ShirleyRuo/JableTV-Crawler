import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import time
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.Crawler import VideoCrawler
from src.Manager import VideoManager, DownloadInfoManager
from src.Config.Config import config
from src.utils.Logger import Logger
from Sender.sender import start_server as start_sender_server
from Sender.SenderConfig import sender_config

class CrawlerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("视频爬虫下载管理器")
        self.geometry("1200x800")
        
        # 初始化组件
        self.video_crawler = None
        self.video_manager = VideoManager()
        self.download_info_manager = None
        self.download_tasks = []
        self.download_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
        # 初始化日志
        self.logger = Logger(config.log_dir).get_logger("CrawlerGUI")
        
        # 创建界面
        self.create_widgets()
        self.setup_style()
        
        # 启动后台线程
        self.start_background_threads()
        
        # 初始化下载信息管理器
        self.init_download_info_manager()
        
    def setup_style(self):
        """设置界面样式"""
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("Treeview", rowheight=25)
        style.configure("Title.TLabel", font=('微软雅黑', 12, 'bold'))
        
    def create_widgets(self):
        """创建所有界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部控制面板
        self.create_control_panel(main_frame)
        
        # 中间内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 左侧：批量下载区域
        left_frame = ttk.LabelFrame(content_frame, text="批量下载")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.create_batch_download_panel(left_frame)
        
        # 中间：下载队列
        center_frame = ttk.LabelFrame(content_frame, text="下载队列")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.create_download_queue_panel(center_frame)
        
        # 右侧：控制面板
        right_frame = ttk.LabelFrame(content_frame, text="控制面板")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.create_control_panel_right(right_frame)
        
        # 底部：日志显示
        bottom_frame = ttk.LabelFrame(main_frame, text="日志")
        bottom_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))
        self.create_log_panel(bottom_frame)
        
    def create_control_panel(self, parent):
        """创建顶部控制面板"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 视频源选择
        source_frame = ttk.LabelFrame(control_frame, text="视频源")
        source_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(source_frame, text="选择源:").pack(side=tk.LEFT, padx=5)
        self.source_var = tk.StringVar(value="jable")
        self.source_combo = ttk.Combobox(source_frame, textvariable=self.source_var, 
                                        width=15, state="readonly")
        self.source_combo.pack(side=tk.LEFT, padx=5)
        
        # 初始化视频源
        self.init_video_sources()
        
        # 视频ID输入
        id_frame = ttk.LabelFrame(control_frame, text="单个下载")
        id_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(id_frame, text="视频ID:").pack(side=tk.LEFT, padx=5)
        self.video_id_entry = ttk.Entry(id_frame, width=30)
        self.video_id_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(id_frame, text="下载", command=self.download_single_video).pack(side=tk.LEFT, padx=5)
        
        # URL输入
        url_frame = ttk.LabelFrame(control_frame, text="URL下载")
        url_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(url_frame, text="视频URL:").pack(side=tk.LEFT, padx=5)
        self.video_url_entry = ttk.Entry(url_frame, width=40)
        self.video_url_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(url_frame, text="下载", command=self.download_from_url).pack(side=tk.LEFT, padx=5)
        
        # 搜索功能
        search_frame = ttk.LabelFrame(control_frame, text="搜索")
        search_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(search_frame, text="关键词:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="搜索", command=self.search_videos).pack(side=tk.LEFT, padx=5)
        
    def create_batch_download_panel(self, parent):
        """创建批量下载面板"""
        # 批量ID输入
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(input_frame, text="批量视频ID（每行一个）:").pack(anchor=tk.W)
        
        self.batch_text = scrolledtext.ScrolledText(input_frame, height=10, width=30)
        self.batch_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="开始批量下载", 
                  command=self.start_batch_download).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空", 
                  command=self.clear_batch_input).pack(side=tk.LEFT, padx=5)
        
        # 示例文本
        example_frame = ttk.LabelFrame(input_frame, text="示例")
        example_frame.pack(fill=tk.X, pady=5)
        
        example_text = "MUKA-003\nMUKA-004\nSDDE-123\nABP-456"
        ttk.Label(example_frame, text=example_text, justify=tk.LEFT).pack(anchor=tk.W, padx=5, pady=5)
        
    def create_download_queue_panel(self, parent):
        """创建下载队列面板"""
        # 队列表格
        columns = ('id', 'source', 'status', 'progress', 'speed', 'time')
        self.queue_tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)
        
        # 配置列
        headers = {
            'id': ('视频ID', 120),
            'source': ('来源', 80),
            'status': ('状态', 100),
            'progress': ('进度', 80),
            'speed': ('速度', 100),
            'time': ('时间', 120)
        }
        
        for col, (text, width) in headers.items():
            self.queue_tree.heading(col, text=text)
            self.queue_tree.column(col, width=width)
        
        # 滚动条
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=vsb.set)
        
        # 布局
        self.queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 控制按钮
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(control_frame, text="暂停选中", 
                  command=self.pause_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="继续选中", 
                  command=self.resume_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="删除选中", 
                  command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="清空队列", 
                  command=self.clear_queue).pack(side=tk.LEFT, padx=5)
        
    def create_control_panel_right(self, parent):
        """创建右侧控制面板"""
        # 发送器控制
        sender_frame = ttk.LabelFrame(parent, text="文件发送器")
        sender_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(sender_frame, text="端口:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.port_entry = ttk.Entry(sender_frame, width=10)
        self.port_entry.insert(0, "5000")
        self.port_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Button(sender_frame, text="启动发送器", 
                  command=self.start_sender).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        # 配置管理
        config_frame = ttk.LabelFrame(parent, text="配置管理")
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(config_frame, text="编辑配置文件", 
                  command=self.edit_config).pack(padx=5, pady=5, fill=tk.X)
        ttk.Button(config_frame, text="重新加载配置", 
                  command=self.reload_config).pack(padx=5, pady=5, fill=tk.X)
        ttk.Button(config_frame, text="打开下载目录", 
                  command=self.open_download_dir).pack(padx=5, pady=5, fill=tk.X)
        
        # 系统信息
        info_frame = ttk.LabelFrame(parent, text="系统信息")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=8, width=30)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.update_system_info()
        
    def create_log_panel(self, parent):
        """创建日志面板"""
        self.log_text = scrolledtext.ScrolledText(parent, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 日志控制按钮
        log_control_frame = ttk.Frame(parent)
        log_control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(log_control_frame, text="清空日志", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_control_frame, text="保存日志", 
                  command=self.save_log).pack(side=tk.LEFT, padx=5)
        
    def init_video_sources(self):
        """初始化视频源列表"""
        try:
            self.video_crawler = VideoCrawler()
            sources = self.video_crawler.avaliable_sources
            self.source_combo['values'] = sources
            if sources:
                self.source_var.set(sources[0])
        except Exception as e:
            self.log_error(f"初始化视频源失败: {e}")
            self.source_combo['values'] = ['jable', 'missav']
            
    def init_download_info_manager(self):
        """初始化下载信息管理器"""
        try:
            download_info_file = config.download_dir / "download_info.json"
            self.download_info_manager = DownloadInfoManager(download_info_file)
        except Exception as e:
            self.log_error(f"初始化下载信息管理器失败: {e}")
            
    def download_single_video(self):
        """下载单个视频"""
        video_id = self.video_id_entry.get().strip()
        if not video_id:
            messagebox.showwarning("警告", "请输入视频ID")
            return
            
        source = self.source_var.get()
        self.add_download_task(video_id, source)
        
    def download_from_url(self):
        """从URL下载视频"""
        url = self.video_url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入视频URL")
            return
            
        # 从URL中提取视频ID
        video_id = self.extract_video_id_from_url(url)
        if not video_id:
            messagebox.showwarning("警告", "无法从URL中提取视频ID")
            return
            
        # 根据URL判断视频源
        source = self.detect_source_from_url(url)
        self.add_download_task(video_id, source, url)
        
    def search_videos(self):
        """搜索视频"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
            
        source = self.source_var.get()
        self.log_info(f"正在搜索: {keyword} (来源: {source})")
        
        # TODO: 实现搜索功能
        messagebox.showinfo("提示", "搜索功能正在开发中")
        
    def start_batch_download(self):
        """开始批量下载"""
        batch_text = self.batch_text.get("1.0", tk.END).strip()
        if not batch_text:
            messagebox.showwarning("警告", "请输入批量视频ID")
            return
            
        video_ids = [line.strip() for line in batch_text.split('\n') if line.strip()]
        source = self.source_var.get()
        
        self.log_info(f"开始批量下载 {len(video_ids)} 个视频 (来源: {source})")
        
        for video_id in video_ids:
            self.add_download_task(video_id, source)
            
    def add_download_task(self, video_id, source, url=None):
        """添加下载任务到队列"""
        task = {
            'id': video_id,
            'source': source,
            'url': url,
            'status': '等待中',
            'progress': 0,
            'speed': '0KB/s',
            'start_time': time.strftime("%H:%M:%S"),
            'thread': None
        }
        
        self.download_tasks.append(task)
        self.download_queue.put(task)
        self.update_queue_display()
        self.log_info(f"已添加下载任务: {video_id} (来源: {source})")
        
    def update_queue_display(self):
        """更新队列显示"""
        # 清空现有显示
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
            
        # 添加任务到显示
        for task in self.download_tasks:
            self.queue_tree.insert('', 'end', values=(
                task['id'],
                task['source'],
                task['status'],
                f"{task['progress']}%",
                task['speed'],
                task['start_time']
            ))
            
    def start_background_threads(self):
        """启动后台线程"""
        # 下载线程
        download_thread = threading.Thread(target=self.download_worker, daemon=True)
        download_thread.start()
        
        # 日志更新线程
        log_thread = threading.Thread(target=self.log_update_worker, daemon=True)
        log_thread.start()
        
    def download_worker(self):
        """下载工作线程"""
        while True:
            try:
                task = self.download_queue.get(timeout=1)
                self.process_download_task(task)
            except queue.Empty:
                continue
            except Exception as e:
                self.log_error(f"下载工作线程错误: {e}")
                
    def process_download_task(self, task):
        """处理下载任务"""
        try:
            task['status'] = '下载中'
            self.update_queue_display()
            
            self.log_info(f"开始下载: {task['id']}")
            
            # 创建爬虫实例
            crawler = VideoCrawler(src=task['source'])
            
            # 模拟下载过程
            for i in range(1, 101):
                time.sleep(0.1)  # 模拟下载时间
                task['progress'] = i
                task['speed'] = f"{i * 10}KB/s"
                self.update_queue_display()
                
            task['status'] = '已完成'
            task['progress'] = 100
            self.update_queue_display()
            self.log_info(f"下载完成: {task['id']}")
            
        except Exception as e:
            task['status'] = '失败'
            self.update_queue_display()
            self.log_error(f"下载失败 {task['id']}: {e}")
            
    def log_update_worker(self):
        """日志更新工作线程"""
        while True:
            try:
                log_entry = self.log_queue.get(timeout=0.5)
                self.log_text.insert(tk.END, log_entry + '\n')
                self.log_text.see(tk.END)
            except queue.Empty:
                continue
                
    def log_info(self, message):
        """记录信息日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[INFO] {timestamp} - {message}"
        self.log_queue.put(log_entry)
        self.logger.info(message)
        
    def log_error(self, message):
        """记录错误日志"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[ERROR] {timestamp} - {message}"
        self.log_queue.put(log_entry)
        self.logger.error(message)
        
    def extract_video_id_from_url(self, url):
        """从URL中提取视频ID"""
        # 简单实现，实际需要根据不同的视频源进行解析
        if 'jable.tv' in url:
            # jable.tv/videos/jufe-589/
            parts = url.rstrip('/').split('/')
            return parts[-1] if parts else None
        elif 'missav' in url:
            # missav.live/cn/muka-003
            parts = url.rstrip('/').split('/')
            return parts[-1] if parts else None
        return None
        
    def detect_source_from_url(self, url):
        """从URL检测视频源"""
        if 'jable.tv' in url:
            return 'jable'
        elif 'missav' in url:
            return 'missav'
        return self.source_var.get()
        
    def start_sender(self):
        """启动发送器服务器"""
        try:
            port = int(self.port_entry.get())
            sender_config.port = port
            sender_config.upload_folder = str(config.download_dir / 'video')
            
            # 在新线程中启动服务器
            server_thread = threading.Thread(target=start_sender_server, daemon=True)
            server_thread.start()
            
            self.log_info(f"发送器服务器已启动，端口: {port}")
            messagebox.showinfo("成功", f"发送器服务器已启动\n端口: {port}\n上传目录: {sender_config.upload_folder}")
        except Exception as e:
            self.log_error(f"启动发送器失败: {e}")
            messagebox.showerror("错误", f"启动发送器失败: {e}")
            
    def edit_config(self):
        """编辑配置文件"""
        try:
            config_file = config.config_dir / "headers.json"
            if config_file.exists():
                os.startfile(str(config_file))
            else:
                messagebox.showinfo("提示", "配置文件不存在")
        except Exception as e:
            self.log_error(f"打开配置文件失败: {e}")
            
    def reload_config(self):
        """重新加载配置"""
        try:
            config.load_headers()
            self.log_info("配置已重新加载")
            messagebox.showinfo("成功", "配置已重新加载")
        except Exception as e:
            self.log_error(f"重新加载配置失败: {e}")
            
    def open_download_dir(self):
        """打开下载目录"""
        try:
            download_dir = config.download_dir
            if download_dir.exists():
                os.startfile(str(download_dir))
            else:
                messagebox.showinfo("提示", "下载目录不存在")
        except Exception as e:
            self.log_error(f"打开下载目录失败: {e}")
            
    def update_system_info(self):
        """更新系统信息"""
        try:
            info = f"项目根目录: {project_root}\n"
            info += f"下载目录: {config.download_dir}\n"
            info += f"临时目录: {config.tmp_dir}\n"
            info += f"日志目录: {config.log_dir}\n"
            info += f"配置目录: {config.config_dir}\n"
            info += f"可用视频源: {', '.join(self.video_crawler.avaliable_sources if self.video_crawler else [])}"
            
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert("1.0", info)
        except Exception as e:
            self.log_error(f"更新系统信息失败: {e}")
            
    def clear_batch_input(self):
        """清空批量输入"""
        self.batch_text.delete("1.0", tk.END)
        
    def clear_queue(self):
        """清空队列"""
        self.download_tasks.clear()
        while not self.download_queue.empty():
            try:
                self.download_queue.get_nowait()
            except queue.Empty:
                break
        self.update_queue_display()
        self.log_info("下载队列已清空")
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", tk.END)
        
    def save_log(self):
        """保存日志"""
        # TODO: 实现保存日志功能
        messagebox.showinfo("提示", "保存日志功能正在开发中")
        
    def pause_selected(self):
        """暂停选中任务"""
        # TODO: 实现暂停功能
        messagebox.showinfo("提示", "暂停功能正在开发中")
        
    def resume_selected(self):
        """继续选中任务"""
        # TODO: 实现继续功能
        messagebox.showinfo("提示", "继续功能正在开发中")
        
    def delete_selected(self):
        """删除选中任务"""
        selected_items = self.queue_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择要删除的任务")
            return
            
        for item in selected_items:
            values = self.queue_tree.item(item, 'values')
            video_id = values[0]
            
            # 从任务列表中移除
            self.download_tasks = [task for task in self.download_tasks if task['id'] != video_id]
            
        self.update_queue_display()
        self.log_info(f"已删除 {len(selected_items)} 个任务")

def main():
    app = CrawlerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()