import json
import logging
import pkgutil
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Type

from .Config.Config import config
from .utils.Logger import Logger
from .Bases.CrawlerBases import VideoCrawlerBase

logger = Logger(config.log_dir).get_logger(__name__, logging.INFO)

class VideoCrawler:
    '''
    视频抓取器

    Args:
        src(str): 视频来源,默认为default,选择default则首先使用jable解析，若失败则按顺序依次解析
        url(str): 视频链接,默认为None
    '''
    def __init__(
            self, 
            src : str = 'default', 
            url : Optional[str] = None,
            ) -> None:
        self._src = src
        self._url = url
        self._avaliable_crawlers : Dict[str, Type[VideoCrawlerBase]] = {}
        try:
            self._load_crawlers_from_conf()
        except (FileNotFoundError, KeyError):
            self._init_crawlers()
            self._dump_crawlers()
    
    def _dump_crawlers(self) -> None:
        '''
        将可用的爬虫类信息存储在缓存文件中
        '''
        data = {domain: crawler.__name__ for domain, crawler in self._avaliable_crawlers.items()}
        with open(config.config_dir / 'crawlers_conf.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def _init_crawlers(self) -> None:
        '''
        初始化加载可用的爬虫类,并将其存储在_avaliable_crawlers字典中
        '''
        crawler_path = Path(__file__).parent / 'Crawlers'
        for module_info in pkgutil.iter_modules([str(crawler_path)]):
            module = importlib.import_module(f'src.Crawlers.{module_info.name}')
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, VideoCrawlerBase) and attr is not VideoCrawlerBase:
                    if attr.domain:
                        self._avaliable_crawlers[attr.domain.split('.')[0]] = attr
                    else:
                        logger.warning(f'爬虫类 {attr_name} 缺少域名属性,无法添加到可用爬虫列表中')

    def _load_crawlers_from_conf(self) -> None:
        '''
        从配置文件中加载可用的爬虫类
        '''
        with open(config.config_dir / 'crawlers_conf.json', 'r') as f:
            data = json.load(f)
        for domain, crawler_name in data.items():
            crawler_path_str = f'src.Crawlers.{crawler_name}'
            module = importlib.import_module(crawler_path_str)
            crawler_class = getattr(module, crawler_name)
            self._avaliable_crawlers[domain] = crawler_class
        
    def clear_log_files(self) -> None:
        '''
        清除日志文件
        '''
        Logger(config.log_dir).clear_log_files()

    def download_video(self, id : str) -> None:
        '''
        根据视频id下载视频

        Args:
            id(str): 视频番号
        '''
        if self._src == 'default':
            src = list(self._avaliable_crawlers.keys())[0]
            crawler = self._avaliable_crawlers[src]()
            crawler.download_video_with_id(video_id=id)
        else:
            Crawler = self._avaliable_crawlers.get(self._src)
            if Crawler:
                crawler = Crawler()
                crawler.download_video_with_id(video_id=id)
            else:
                logger.error(f'不支持的视频来源: {self._src}')
                logger.info(f'可用的视频来源: {self._avaliable_crawlers.keys()}')
                raise ValueError(f'不支持的视频来源: {self._src}')
            
    def search_video(self, keyword : str) -> None:
        '''
        根据关键字搜索视频
        Args:
            keyword(str): 搜索关键字
        '''
        pass

    def search_videos_with_tag(self, tag : str) -> None:
        '''
        根据标签搜索视频
        Args:
            tag(str): 标签
        '''
        pass

    def multi_download(self, ids : List[str]) -> None:
        '''
        根据视频id列表下载视频

        Args:
            ids(List[str]): 视频番号列表
        '''
        if self._src == 'default':
            src = list(self._avaliable_crawlers.keys())[0]
            crawler = self._avaliable_crawlers[src]()
            crawler.multi_download(ids=ids)
        else:
            Crawler = self._avaliable_crawlers.get(self._src)
            if Crawler:
                crawler = Crawler()
                crawler.multi_download(ids=ids)
            else:
                logger.error(f'不支持的视频来源: {self._src}')
                logger.info(f'可用的视频来源: {self._avaliable_crawlers.keys()}')
                raise ValueError(f'不支持的视频来源: {self._src}')
    
    @property
    def avaliable_sources(self) -> List[str]:
        '''
        可用的视频来源列表
        '''
        return list(self._avaliable_crawlers.keys())