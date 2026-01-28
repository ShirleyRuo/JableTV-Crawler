import sys
sys.path.append(r'd:\桌面\Video')

from src.Crawler import MissavVideoCrawler,JabVideoCrawler

crawler = JabVideoCrawler()
crawler.muti_download(['dass-777','mmks-032'])