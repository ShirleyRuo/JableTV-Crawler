import time
from threading import Thread
import requests
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, Union, List


from ..utils.EnumType import Page
from ..utils.Logger import Logger
from ..Config.Config import config
from ..Error.Exception import NotFoundError, ForbiddenError
from ..PageParse.utils.PageValidation import validation
from ..utils.DataUnit import DownloadPackage
from ..Downloader import Downloader

logger = Logger(config.log_dir).get_logger(__name__)

class VideoCrawlerBaseMeta(ABCMeta):

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if name != 'VideoCrawlerBase':
            if not hasattr(cls, '_crawler_registry'):
                cls._crawler_registry = {}
            domain_id = getattr(cls, 'domain', name.lower().replace('videocrawler', ''))
            src = domain_id.split('.')[0]
            cls._crawler_registry[src] = cls

class VideoCrawlerBase(ABC):

    domain : str | None = None
    path_to_video : str | None = None

    def __init__(
            self,
            *,
            protocol : str = 'https://', 
            path : Union[str, None] = None,
            parameters : Union[str, None] = None,
            query_params : Union[Dict, None] = None,
            ) -> None:
        '''
        Args:
            path (Union[str, None], optional): 站点路径. Defaults to None.
            parameters (Union[str, None], optional): 站点参数. Defaults to None.
            query_params (Union[Dict, None], optional): 站点查询参数. Defaults to None.
        '''
        self.protocol = protocol
        self._domain = self._get_domain()
        self.path = path
        self.parameters = parameters
        self.query_params = query_params
        self.url = self._construct_url()
        self._download_list = []
    
    @classmethod
    def _get_domain(cls) -> str:
        if cls.domain:
            return cls.domain
        else:
            raise NotImplementedError('请在子类中定义domain属性')

    def _construct_url(self) -> str:
        url = self.protocol + self._domain
        if self.path:
            url += self.path
        if self.parameters:
            url += self.parameters
        if self.query_params:
            query_string = '&'.join([f"{key}={value}" for key, value in self.query_params.items()])
            url += '?' + query_string
        return url

    def _get_headers(self, **kwargs) -> None:
        '''
        设置请求头
        Args:
            **kwargs: 请求头参数
        Returns:
            None
        Raises:
            ValueError: 不支持的视频网站
        '''
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Origin' : f'{self.protocol}{self.domain}',
            'Referer' : f'{self.protocol}{self.domain}/',
            'Priority' : 'u=1, i',
        }
        headers.update({**kwargs})
        try:
            config.load_headers()
            logger.info(f'加载请求头成功!')
        except FileNotFoundError:
            pass
        config.headers.update(headers)

    # @abstractmethod
    # def _set_proxy(self) -> None:
    #     raise NotImplementedError

    @abstractmethod
    def _parse_page_content(self, html_text : str) -> Any:
        raise NotImplementedError
    
    @abstractmethod
    def parse(self) -> DownloadPackage:
        raise NotImplementedError
    
    def _init_download_package(self, package_info_dict : Dict[str, Any]) -> DownloadPackage:
        package = DownloadPackage(
            id = package_info_dict['id'],
            name = package_info_dict['name'],
            actress = package_info_dict['actress'],
            hash_tags = package_info_dict['hash_tags'],
            hls_url = package_info_dict['hls_url'],
            cover_url = package_info_dict['cover_url'],
            src = self.src,
            time_length=package_info_dict['time_length'],
            release_date=package_info_dict['release_date'],
            has_chinese=package_info_dict['has_chinese'],
        )
        return package
    
    def _get_html_text(self) -> str:
        '''
        获取html文本

        Returns:
            str: html文本
        Raises:
            NotFoundError: 请求视频页面不存在
            ForbiddenError: 请求视频页面被禁止
            Exception: 请求视频页面失败
        '''
        self._get_headers()
        # self._set_proxy()
        NotFound_count = 0
        for retry_count in range(config.max_retries):
            try:
                response = requests.get(self.url, headers=config.headers, proxies=config.proxies, timeout=10)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 403:
                    if self._parse_page_content(response.text) == Page.CAPTACHA:
                        logger.info(f'请求视频页面被拦截,正在验证...')
                        if html_text := validation(self.url):
                            logger.info(f'验证成功,继续请求...')
                            cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
                            config.headers.update({'Cookie': '; '.join(cookies_list)})
                            config.save_headers()
                            return html_text
                        else:
                            logger.error('验证失败')
                            raise ForbiddenError('验证失败')
                    logger.error(f'请求视频页面被禁止: {response.status_code}')
                    raise ForbiddenError(f'请求视频页面被禁止: {response.status_code}')
                elif response.status_code == 404:
                    NotFound_count += 1
                    logger.warning(f'请求视频页面不存在: {response.status_code}')
                else:
                    logger.error(f'请求视频页面失败: {response.status_code},正在重试...')
            except requests.exceptions.RequestException as e:
                logger.error(f'请求视频页面失败: {e},正在重试...')
                if 'ConnectionResetError(10054' in str(e):
                    if html_text := validation(self.url):
                        logger.info(f'验证成功,继续请求...')
                        cookies_list = [f"{cookies['name']}={cookies['value']}" for cookies in config.cookie]
                        config.headers.update({'Cookie': '; '.join(cookies_list)})
                        config.save_headers()
                        return html_text
                    else:
                        logger.error('验证失败,继续重试...')
            wait_time = config.retry_wait_time * (2 ** retry_count + 1)
            logger.info(f'等待 {wait_time} 秒后重试...')
            time.sleep(wait_time)
        logger.error(f'请求视频页面失败: 超过最大重试次数')
        if NotFound_count >= config.max_retries:
            raise NotFoundError(f'请求视频页面不存在: {response.status_code}')
        raise Exception(f'请求视频页面失败: 超过最大重试次数')
    
    def _download_video(self) -> None:
        package = self.parse()
        downloader = Downloader(package)
        downloader.download()
    
    def download_video_with_id(self, video_id : str) -> None:
        if self.path_to_video:
            self.path = self.path_to_video
        else:
            raise NotImplementedError('请在子类中定义path_to_video属性或重写download_video_with_id方法')
        self.parameters = f"{video_id}/"
        self.url = self._construct_url()
        self._download_video()
    
    def _add_task(self, download_package : DownloadPackage) -> None:
        self._download_list.append(download_package)
    
    def _display_tasks(self, downloader : Downloader, wait_time : int = 1) -> None:
        total = ''
        for name, counter in downloader._counters.items():
            total += f"\r{name} : {counter.current_id} / {counter.total_num}\n"
        print(total, end='')
        time.sleep(wait_time)

    def _run_tasks(self) -> None:
        if self._download_list:
            downloader = Downloader(self._download_list)
            task = Thread(target=self._display_tasks, args=(downloader, 5))
            task.start()
            downloader.download()
        else:
            logger.error('下载列表为空')
            raise ValueError('下载列表为空')
    
    def muti_download(
            self, 
            ids : List[str],
            quiet : bool = False,
            ) -> None:
        if quiet:
            Logger(config.log_dir).disable_stream_handler('src.Downloader')
        for id in ids:
            if self.path_to_video:
                self.path = self.path_to_video
            else:
                raise NotImplementedError('请在子类中定义path_to_video属性或重写download_video_with_id方法')
            self.parameters = f"{id}/"
            self.url = self._construct_url()
            package = self.parse()
            self._add_task(package)
        self._run_tasks()    
    
    @property
    def src(self) -> str:
        return self.domain.split('.')[0]