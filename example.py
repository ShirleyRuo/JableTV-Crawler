from src.Crawler import VideoCrawler

if __name__ == '__main__':
    video_crawler = VideoCrawler(src='missav')
    video_crawler.download_video('MUKA-003')