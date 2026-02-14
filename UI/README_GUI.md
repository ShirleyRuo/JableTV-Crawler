# 视频爬虫下载管理器 GUI

这是一个基于tkinter的图形用户界面，用于管理视频爬虫下载任务。

## 功能特性

1. **多视频源支持**
   - jable.tv
   - missav.live
   - 自动检测可用视频源

2. **下载管理**
   - 单个视频下载
   - 批量视频下载
   - URL直接下载
   - 下载队列管理

3. **文件发送器**
   - 启动Web服务器
   - 通过浏览器发送文件到移动设备
   - 支持大文件分块上传

4. **配置管理**
   - 编辑配置文件
   - 重新加载配置
   - 打开下载目录

5. **日志系统**
   - 实时日志显示
   - 日志保存功能

## 快速开始

### 方法1: 使用批处理文件 (Windows)
双击 `start_gui.bat`

### 方法2: 使用PowerShell脚本 (Windows)
右键点击 `start_gui.ps1`，选择"使用PowerShell运行"

### 方法3: 手动启动
```bash
cd UI
python crawler_gui.py
```

## 系统要求

- Python 3.6 或更高版本
- tkinter (通常随Python一起安装)
- 项目依赖 (见 requirements.txt)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用指南

### 1. 下载单个视频
1. 在"视频源"下拉框中选择视频源
2. 在"单个下载"输入框中输入视频ID (如: MUKA-003)
3. 点击"下载"按钮

### 2. 批量下载视频
1. 在左侧"批量下载"区域输入视频ID，每行一个
2. 点击"开始批量下载"按钮

### 3. 从URL下载
1. 在"URL下载"输入框中输入视频URL
2. 点击"下载"按钮
3. 系统会自动提取视频ID和检测视频源

### 4. 使用文件发送器
1. 在右侧控制面板的"文件发送器"部分
2. 输入端口号 (默认: 5000)
3. 点击"启动发送器"按钮
4. 按照提示在浏览器中访问显示的地址

### 5. 管理下载队列
- **暂停选中**: 暂停选中的下载任务
- **继续选中**: 继续选中的下载任务
- **删除选中**: 删除选中的下载任务
- **清空队列**: 清空所有下载任务

## 配置文件

配置文件位于 `conf/` 目录下:
- `headers.json`: HTTP请求头配置
- `crawlers_conf.json`: 爬虫配置
- `parameters.json`: 参数配置

## 目录结构

- `downloads/`: 下载的视频文件
- `logs/`: 日志文件
- `tmp/`: 临时文件
- `assets/`: 资源文件
- `conf/`: 配置文件

## 故障排除

### 1. 导入错误
确保项目根目录在Python路径中:
```python
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

### 2. tkinter未安装
在Windows上，tkinter通常随Python一起安装。如果未安装，可以重新安装Python并确保选中"tcl/tk and IDLE"选项。

### 3. 依赖未安装
运行以下命令安装所有依赖:
```bash
pip install -r requirements.txt
```

### 4. 目录权限问题
确保程序有权限读写以下目录:
- downloads/
- logs/
- tmp/

## 开发说明

### 添加新的视频源
1. 在 `src/Crawlers/` 目录下创建新的爬虫类
2. 继承 `VideoCrawlerBase` 基类
3. 实现必要的接口方法
4. GUI会自动检测并添加新的视频源

### 扩展GUI功能
1. 在 `CrawlerGUI` 类中添加新的方法
2. 在 `create_widgets` 方法中添加对应的界面组件
3. 绑定事件处理函数

## 许可证

本项目基于MIT许可证。

## 支持

如有问题或建议，请提交Issue或联系开发者。