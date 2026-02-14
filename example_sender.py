'''

    这里展示了如何使用局域网创建文件传输系统


    当想使用电脑下载好的视频进行传输时，使用如下：
    from src.Manager import VideoManager

    video_manager = VideoManager()
    video_manager.send_to_mobile()

    问题解决方案：
    1.出现ModuleNotFoundError时，若为第三方库，请使用pip install；若为自定义模块尝试使用：
    import sys
    sys.path.append('path/to/your/module')
'''

from Sender.sender import start_server

start_server()

