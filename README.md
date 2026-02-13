# 视频下载工具

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

一个功能强大的视频下载工具，支持从多个视频网站自动下载视频。本项目采用模块化设计，支持TS分片下载、文件解密、自动合并等功能。

## 功能特性

### 核心功能
- ✅ **多视频源支持**：支持Jable.TV和Missav等多个视频网站
- ✅ **智能页面解析**：自动解析视频ID、标题、演员、HLS地址、封面等信息
- ✅ **TS分片多线程下载**：高效下载视频TS分片，支持断点续传
- ✅ **文件完整性校验**：基于16位块大小检测，确保文件完整性
- ✅ **AES解密支持**：自动解密加密的TS视频分片
- ✅ **自动合并TS文件**：支持原生合并和FFmpeg加速合并两种模式
- ✅ **智能重试机制**：指数退避算法，提高下载成功率
- ✅ **重复文件处理**：基于时间戳自动重命名重复文件

### 高级功能
- 🔄 **断点续传**：支持下载中断后从断点继续下载
- 🛡️ **代理支持**：可配置代理服务器，绕过访问限制
- 📊 **详细日志**：完整的日志记录，便于调试和监控
- 🧩 **模块化设计**：易于扩展新的视频源和功能

## 安装和使用

### 前置要求
- Python 3.8+
- FFmpeg（可选，用于加速合并）

### 安装步骤
1. 克隆项目到本地：
   ```bash
   git clone <repository-url>
   cd Video
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. （可选）安装FFmpeg以加速视频合并：
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # 从 https://ffmpeg.org/download.html 下载并添加到PATH
   ```

### 基本使用
```python
from src.Crawler import VideoCrawler

# 下载Missav视频
video_crawler = VideoCrawler(src='missav')
video_crawler.download_video('MUKA-003')

# 下载Jable视频（默认源）
video_crawler = VideoCrawler(src='jable')
video_crawler.download_video('GVH-778')
```

### 命令行使用
项目提供了示例脚本，您也可以创建自己的脚本：
```python
# 参考 example.py 和 example_sender.py
```

## 项目结构

```
project-root/
├── src/                          # 核心源代码
│   ├── Crawler.py               # 视频爬虫调度器
│   ├── Downloader.py            # TS下载/合并核心逻辑
│   ├── Manager.py               # 下载管理器
│   ├── Bases/                   # 基础类定义
│   │   ├── CrawlerBases.py     # 爬虫基类
│   │   ├── VideoBases.py       # 视频基类
│   │   └── PageParserBase.py   # 页面解析器基类
│   ├── Crawlers/               # 具体爬虫实现
│   │   ├── JabVideoCrawler.py  # Jable爬虫
│   │   └── MissavVideoCrawler.py # Missav爬虫
│   ├── PageParse/              # 页面解析模块
│   │   ├── JabPageParser/      # Jable页面解析
│   │   └── MissavPageParser/   # Missav页面解析
│   ├── Config/                 # 配置管理
│   ├── utils/                  # 工具函数
│   ├── encoder/                # 编码相关
│   └── decoder/                # 解码相关
├── Sender/                     # 文件传输模块（Web界面）
│   ├── sender.py              # Web服务主模块
│   ├── SenderConfig.py        # 发送器配置
│   └── static/                # 前端资源
├── conf/                       # 配置文件目录
│   ├── crawlers_conf.json     # 爬虫配置
│   ├── headers.json           # HTTP头配置
│   └── parameters.json        # 参数配置
├── assets/                     # 资源文件
│   ├── actress_id.json        # 演员ID映射
│   ├── headers.json           # 备用HTTP头
│   └── tag_mapping.json       # 标签映射
├── downloads/                  # 下载文件存储目录
├── logs/                       # 日志目录
├── test_files/                 # 测试文件
├── requirements.txt            # Python依赖
├── example.py                  # 使用示例
└── example_sender.py           # 发送器示例
```

## 配置说明

### 爬虫配置
编辑 `conf/crawlers_conf.json` 配置支持的视频源：
```json
{
    "jable": "JabVideoCrawler",
    "missav": "MissavVideoCrawler"
}
```

### HTTP头配置
编辑 `conf/headers.json` 配置请求头，避免被网站屏蔽：
```json
{
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}
```

### 代理配置
在代码中配置代理服务器：
```python
# 在您的脚本中设置代理
from src.Config.Config import config
config.proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
```

## 注意事项

### 法律和道德
1. **请遵守当地法律法规**：仅下载您有权访问的视频内容
2. **尊重版权**：不要将下载的内容用于商业用途或非法分发
3. **合理使用**：避免对目标网站造成过大负载

### 技术限制
1. **网站结构变化**：如果目标网站更新页面结构，可能需要更新解析逻辑
2. **访问限制**：某些网站可能有反爬虫机制，需要使用代理或调整请求频率
3. **网络环境**：下载速度受网络环境和目标服务器限制

### 故障排除
1. **下载失败**：检查网络连接、代理配置和目标URL有效性
2. **文件损坏**：启用完整性校验，或尝试重新下载
3. **解析错误**：检查页面解析器是否与网站当前结构匹配

## 开发指南

### 添加新的视频源
1. 在 `src/Crawlers/` 目录下创建新的爬虫类，继承 `VideoCrawlerBase`
2. 在 `src/PageParse/` 目录下创建对应的页面解析器
3. 在 `conf/crawlers_conf.json` 中添加新的视频源配置
4. 更新 `src/Crawler.py` 中的爬虫加载逻辑

### 扩展功能
1. **新的下载协议**：在 `src/Downloader.py` 中添加支持
2. **新的文件格式**：在 `src/encoder/` 和 `src/decoder/` 中添加编解码器
3. **监控和统计**：扩展 `src/utils/` 中的工具类

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 免责声明

本项目仅用于学习和研究目的。使用者应对自己的行为负责，作者不对任何因使用本项目而产生的法律问题负责。