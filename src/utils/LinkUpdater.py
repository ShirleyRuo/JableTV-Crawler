'''
当网站无法打开时，根据网址名称，更新网站首页的链接。
'''
from Bases.CrawlerBases import VideoCrawlerBase

class LinkUpdater:

    def __init__(self, crawler: VideoCrawlerBase) -> None:
        self.crawler = crawler
    
    def _update_missav_link(self) -> None:
        # TODO
        pass
    
    def _update_jab_link(self) -> None:
        # TODO
        pass

    def update(self) -> None:
        if self.crawler.src == 'missav':
            self._update_missav_link()
        elif self.crawler.src == 'jable':
            self._update_jab_link()
        else:
            raise NotImplementedError(f'不支持的站点: {self.crawler.src}')