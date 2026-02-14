import logging
from typing import Any

from ..Config.Config import config
from ..utils.Logger import Logger
from ..utils.EnumType import Page
from ..Bases.CrawlerBases import VideoCrawlerBase
from ..PageParse.MissavPageParser.MissavPageParser import MissavPageParser

logger = Logger(config.log_dir).get_logger(__name__, logging.INFO)

class MissavVideoCrawler(VideoCrawlerBase):

    domain = 'missav.live'
    path_to_video = '/cn/'
    
    def __init__(
            self, 
            ) -> None:
        super().__init__()
        self._download_list = []
    
    def _parse_page_content(self, html_text : str | None = None) -> Page:
        if html_text:
            if 'just a moment' in html_text.lower():
                return Page.CAPTACHA
            else:
                logger.error('未知错误')
                raise ValueError('未知错误')
        return Page.SINGLE_VIDEO

    def parse(self) -> Any:
        '''
        解析html页面,根据页面信息返回不同操作

        Returns:
            DownloadPackage: 下载信息
        '''
        page = self._parse_page_content()
        if page == Page.SINGLE_VIDEO:
            html_text = self._get_html_text()
            logger.info(f"解析页面: \n{html_text[:500]}")
            parser = MissavPageParser(html_text)
            pacakge_info_dict = parser.parse()
            if pacakge_info_dict is None:
                pacakge_info_dict = {}
            return self._init_download_package(pacakge_info_dict)
        else:
            logger.error(f'不支持的视频链接: {self.url}')
            raise ValueError(f'不支持的视频链接: {self.url}')