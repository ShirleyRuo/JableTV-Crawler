'''

    这里展示了如何使用VideoCrawler类来下载视频。可以根据需要修改视频来源和视频番号。
    下载时请打开科学上网，并确认网络通畅

    
    1.查看视频源
    video_crawler = VideoCrawler()
    print(video_crawler.avaliable_sources)

    2.下载单个视频
    video_crawler = VideoCrawler(src='jable')
    video_crawler.download_video('MUKA-003')

    3.当下载多个视频时：
    video_crawler = VideoCrawler(src='jable')
    video_crawler.multi_download(['MUKA-003', 'MUKA-004'])

    4.清理日志文件：
    video_crawler.clear_log_files()

    问题解决方案：
    1.出现ModuleNotFoundError时，若为第三方库，请使用pip install；若为自定义模块尝试使用：
    import sys
    sys.path.append('path/to/your/module')

    2.打开selenium失败，请确认已安装selenium库，并且已下载对应浏览器的驱动程序，并将其路径添加到系统环境变量中
    初次运行时可能会需要一定时间加载,第一次失败后请重试
'''

from src.Crawler import VideoCrawler

video_crawler = VideoCrawler(src='missav')
video_crawler.download_video('MIKR-074')