import os

import time
import json
import logging
from pathlib import Path
import pkgutil
import requests
import importlib
from collections import namedtuple
from typing import Dict, List, Any, Optional, Tuple, Union, Type

from .Config.Config import config
from .utils.Logger import Logger
from .utils.EnumType import Page
from .Crawlers.JabVideoCrawler import JabVideoCrawler
from .Crawlers.MissavVideoCrawler import MissavVideoCrawler
from .PageParse.JabPageParser.JabActressId import JabActressId
from .utils.DataUnit import DownloadPackage, VideoPackage
from .PageParse.JabPageParser.JabPageParser import JabPageParser
from .PageParse.JabPageParser.JabTagMapping import JabTagParser
from .PageParse.utils.PageValidation import validation
from .PageParse.MissavPageParser.MissavPageParser import MissavPageParser
from .Error.Exception import ForbiddenError, NotFoundError
from .Downloader import Downloader
from .Bases.CrawlerBases import VideoCrawlerBase

logger = Logger(config.log_dir).get_logger(__name__, logging.INFO)

# class JabVideoCrawler(VideoCrawlerBase):
    
#     path_to_video = '/videos/'

#     def __init__(
#             self, 
#             domain : str = 'jable.tv',
#             videos_per_page : int = 24,
#             ):
#         super().__init__(domain=domain)
#         self.videos_per_page = videos_per_page
#         self._download_list = []
              
#     def _parse_page_content(
#             self,
#             html_text : str | None = None,
#             ) -> Page:
#         '''
#         获取页面类型
#         Args:
#             html_text(str): 页面文本,默认为None
#         Returns:
#             Page: 页面类型
#         Raises:
#             ValueError: 不支持的视频链接
#         '''
#         if html_text:
#             if 'just a moment' in html_text.lower():
#                 return Page.CAPTACHA
#             else:
#                 logger.error('未知错误')
#                 raise ValueError('未知错误')
#         if 'videos' in self.url:
#             return Page.SINGLE_VIDEO
#         else:
#             logger.error(f'不支持的视频链接: {self.url}')
#             raise ValueError(f'不支持的视频链接: {self.url}')
    
#     def parse(self) -> Any:
#         '''
#         解析html页面,根据页面信息返回不同操作

#         Returns:
#             DownloadPackage: 下载包
#         '''
#         page = self._parse_page_content()
#         if page == Page.SINGLE_VIDEO:
#             html_text = self._get_html_text()
#             _actress_id = JabActressId(html_text=html_text)
#             _actress_id._parse()
#             _actress_id._dump()
#             logger.info(f"解析页面: \n{html_text[:500]}")
#             parser = JabPageParser(html_text)
#             package_info_dict = parser.parse()
#             if package_info_dict is None:
#                 package_info_dict = {}
#             return self._init_download_package(package_info_dict)
#         else:
#             logger.error(f'不支持的视频链接: {self.url}')
    
#     def _tag2link(
#             self,
#             tag_title : str,
#             tag : str,
#     ) -> str | None:
#         '''
#         根据标签名称获取标签链接,用于标签名固定的情况下使用

#         Args:
#             tag_title(str): 标签名称
#             tag(str): 标签关键词
#         Returns:
#             str: 标签链接
#         '''
#         _tag_parser = JabTagParser()
#         tag_title, tag = _tag_parser._input_tag2_hant(tag_title, tag)
#         if os.path.exists(config.assets_dir / 'tag_mapping.json'):
#             with open(config.assets_dir / 'tag_mapping.json', 'r', encoding='utf-8') as f:
#                 tag_mapping = json.load(f)
#             if 'jable' in tag_mapping:
#                 tags : Dict = tag_mapping['jable']
#                 if tag_title in tags:
#                     if tag in tags[tag_title]:
#                         return f'https://jable.tv/tags/{tags[tag_title][tag]}/'
#                     else:
#                         logger.error(f"{tag} 不在 {tag_title} 标签下")
#                         raise ValueError(f"{tag} 不在 {tag_title} 标签下")
#                 else:
#                     logger.error(f'不支持的标签: {tag_title}')
#                     raise ValueError(f'不支持的标签: {tag_title}')
#         else:
#             logger.error(f'标签映射文件不存在: {config.assets_dir / "tag_mapping.json"}')
#             raise FileNotFoundError(f'标签映射文件不存在: {config.assets_dir / "tag_mapping.json"}')
    
#     def _search(self, search_word : str) -> Tuple[int, int, Union[List[VideoPackage], None]]:
#         '''
#         根据提供的标签关键词搜索视频,返回搜索得到的视频数和页数以及第一页视频.
#         '''
#         SearchInfo = namedtuple('SearchInfo', ['videos', 'pages', 'first_page_videos'])
#         parser = JabPageParser()
#         search_api = f'https://jable.tv/search/{search_word}'
#         for retry_count in range(config.max_retries):
#             try:
#                 response = requests.get(search_api, headers=config.headers, proxies=config.proxies, timeout=10)
#                 if response.status_code == 200:
#                     html_text = response.text
#                     parser._html_text = html_text
#                     videos = parser._parse_videos_num()
#                     video_list = parser.parse()
#                     pages, remainder = divmod(videos, self.videos_per_page)
#                     if remainder > 0:
#                         pages += 1
#                     logger.info(f'搜索成功!')
#                     return SearchInfo(videos=videos, pages=pages, first_page_videos=video_list)
#                 elif response.status_code == 404:
#                     logger.error(f'搜索失败: {response.status_code}')
#                     raise NotFoundError(f'搜索失败: {response.status_code}')
#                 elif response.status_code == 403:
#                     logger.info(f"请求搜索页面被拦截,正在验证...")
#                     if html_text := validation(search_api):
#                         logger.info(f"验证成功,继续请求...")
#                         cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
#                         config.headers.update({'Cookie': '; '.join(cookies_list)})
#                         parser._html_text = html_text
#                         videos = parser._parse_videos_num()
#                         video_list = parser.parse()
#                         pages, remainder = divmod(videos, self.videos_per_page)
#                         if remainder > 0:
#                             pages += 1
#                         logger.info(f'搜索成功!')
#                         return SearchInfo(videos=videos, pages=pages, first_page_videos=video_list)
#                     else:
#                         logger.error(f"验证失败")
#                         raise ForbiddenError(f"验证失败")
#                 else:
#                     logger.error(f'搜索失败: {response.status_code}')
#                     raise Exception(f'搜索失败: {response.status_code}')
#             except requests.exceptions.RequestException as e:
#                 wait_time = config.retry_wait_time * (2 ** retry_count + 1)
#                 logger.info(f'搜索失败: 等待 {wait_time} 秒后重试...')
#                 time.sleep(wait_time)
#                 continue
        
#     def _search_with_tag(
#             self, 
#             tag_title : str,
#             tag : str,
#             ) -> Tuple[str, int, List[VideoPackage]]:
#         '''
#         根据提供的标签关键词搜索视频,返回标签对应的url,页数以及第一页视频.
#         '''
#         TagInfo = namedtuple('TagInfo', ['url', 'pages', 'videos'])
#         parser = JabPageParser()
#         search_api = self._tag2link(tag_title, tag)
#         for retry_count in range(config.max_retries):
#             try:
#                 response = requests.get(search_api, headers=config.headers, proxies=config.proxies, timeout=10)
#                 if response.status_code == 200:
#                     html_text = response.text
#                     parser._html_text = html_text
#                     videos = parser._parse_videos_num()
#                     video_list = parser.parse()
#                     pages, remainder = divmod(videos, self.videos_per_page)
#                     if remainder > 0:
#                         pages += 1
#                     tag_info = TagInfo(url=search_api, pages=pages, videos=video_list)
#                     logger.info(f'搜索成功!')
#                     return tag_info
#                 elif response.status_code == 404:
#                     logger.error(f'搜索失败: {response.status_code}')
#                     raise NotFoundError(f'搜索失败: {response.status_code}')
#                 elif response.status_code == 403:
#                     logger.info(f"请求搜索页面被拦截,正在验证...")
#                     if html_text := validation(search_api):
#                         logger.info(f"验证成功,继续请求...")
#                         cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
#                         config.headers.update({'Cookie': '; '.join(cookies_list)})
#                         parser._html_text = html_text
#                         videos = parser._parse_videos_num()
#                         video_list = parser.parse()
#                         pages, remainder = divmod(videos, self.videos_per_page)
#                         if remainder > 0:
#                             pages += 1
#                         tag_info = TagInfo(url=search_api, pages=pages, videos=video_list)
#                         logger.info(f'搜索成功!')
#                         return tag_info
#                     else:
#                         logger.error(f"验证失败")
#                         raise ForbiddenError(f"验证失败")
#                 else:
#                     logger.error(f'搜索失败: {response.status_code}')
#                     raise Exception(f'搜索失败: {response.status_code}')
#             except requests.exceptions.RequestException as e:
#                 wait_time = config.retry_wait_time * (2 ** retry_count + 1)
#                 logger.info(f'搜索失败: 等待 {wait_time} 秒后重试...')
#                 time.sleep(wait_time)
#                 continue

# class MissavVideoCrawler(VideoCrawlerBase):

#     path_to_video = '/cn/'
    
#     def __init__(
#             self, 
#             domain : str = 'missav.live',
#             ):
#         super().__init__(domain=domain)
#         self._download_list = []
#         self._use_proxies = False
    
#     def _parse_page_content(self, html_text : str | None = None) -> Page:
#         if html_text:
#             if 'just a moment' in html_text.lower():
#                 return Page.CAPTACHA
#             else:
#                 logger.error('未知错误')
#                 raise ValueError('未知错误')
#         return Page.SINGLE_VIDEO
  
#     # def _get_headers(self) -> None:
#     #     headers = {
#     #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
#     #         'Origin' : 'https://missav.live',
#     #         'Priority' : 'u=1, i',
#     #     }
#     #     config.headers.update(headers)
    
#     def _set_proxy(self) -> None:
#         if self._use_proxies:
#             pass
#         else:
#             config.disable_proxies()

#     def parse(self) -> Any:
#         '''
#         解析html页面,根据页面信息返回不同操作

#         Returns:
#             DownloadPackage: 下载信息
#         '''
#         page = self._parse_page_content()
#         if page == Page.SINGLE_VIDEO:
#             html_text = self._get_html_text()
#             logger.info(f"解析页面: \n{html_text[:500]}")
#             parser = MissavPageParser(html_text)
#             pacakge_info_dict = parser.parse()
#             if pacakge_info_dict is None:
#                 pacakge_info_dict = {}
#             return self._init_download_package(pacakge_info_dict)
#         else:
#             logger.error(f'不支持的视频链接: {self.url}')

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

    def download_video(self, id : str) -> None:
        '''
        根据视频id下载视频

        Args:
            id(str): 视频番号
        '''
        if self._src == 'default':
            pass
        else:
            Crawler = self._avaliable_crawlers.get(self._src)
            if Crawler:
                crawler = Crawler()
                crawler.download_video_with_id(video_id=id)
            else:
                logger.error(f'不支持的视频来源: {self._src}')
                raise ValueError(f'不支持的视频来源: {self._src}')
            
    def search_video(self, keyword : str) -> None:
        '''
        根据关键字搜索视频
        Args:
            keyword(str): 搜索关键字
        '''
        pass

    def multi_download(self, ids : List[str]) -> None:
        '''
        根据视频id列表下载视频

        Args:
            ids(List[str]): 视频番号列表
        '''
        if self._src == 'default':
            pass
        else:
            Crawler = self._avaliable_crawlers.get(self._src)
            if Crawler:
                crawler = Crawler()
                crawler.muti_download(ids=ids)
            else:
                logger.error(f'不支持的视频来源: {self._src}')
                raise ValueError(f'不支持的视频来源: {self._src}')