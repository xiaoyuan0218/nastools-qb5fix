import json
import os
import re
import traceback
from pathlib import Path

import log
from app.downloader import Downloader
from app.downloader.client import Qbittorrent, Transmission
from app.media import Media
from app.media.meta import MetaInfo
from app.message import Message
from app.searcher import Searcher
from app.sites import Sites
from app.utils import Torrent
from app.utils.commons import singleton
from app.utils.types import SearchType
from config import Config
from web.backend.search_torrents import SearchTorrents
from web.backend.user import current_user


@singleton
class WebAction(object):

    # ... (all other methods remain the same, only modifying __download and __download_link)

    def __download(self, data):
        """
        从WEB添加下载
        """
        dl_id = data.get("id")
        dl_dir = data.get("dir")
        dl_setting = data.get("setting")
        results = self.dbhelper.get_search_result_by_id(dl_id)
        for res in results:
            media = Media().get_media_info(title=res.TORRENT_NAME, subtitle=res.DESCRIPTION)
            if not media:
                continue
            media.set_torrent_info(enclosure=res.ENCLOSURE,
                                   size=res.SIZE,
                                   site=res.SITE,
                                   page_url=res.PAGEURL,
                                   upload_volume_factor=float(
                                       res.UPLOAD_VOLUME_FACTOR),
                                   download_volume_factor=float(res.DOWNLOAD_VOLUME_FACTOR))
            # 添加下载
            ret, ret_msg = Downloader().download(media_info=media,
                                                 download_dir=dl_dir,
                                                 download_setting=dl_setting)
            if ret:
                # 发送消息
                media.user_name = current_user.username
                Message().send_download_message(in_from=SearchType.WEB,
                                                can_item=media)
            else:
                # 发送下载失败通知
                Message().send_download_fail_message(download_item=media, error_msg=ret_msg)
                return {"retcode": -1, "retmsg": ret_msg}
        return {"retcode": 0, "retmsg": ""}

    @staticmethod
    def __download_link(data):
        """
        从WEB添加下载链接
        """
        site = data.get("site")
        enclosure = data.get("enclosure")
        title = data.get("title")
        description = data.get("description")
        page_url = data.get("page_url")
        size = data.get("size")
        seeders = data.get("seeders")
        uploadvolumefactor = data.get("uploadvolumefactor")
        downloadvolumefactor = data.get("downloadvolumefactor")
        dl_dir = data.get("dl_dir")
        dl_setting = data.get("dl_setting")
        if not title or not enclosure:
            return {"code": -1, "msg": "种子信息有误"}
        media = Media().get_media_info(title=title, subtitle=description)
        media.site = site
        media.enclosure = enclosure
        media.page_url = page_url
        media.size = size
        media.upload_volume_factor = float(uploadvolumefactor)
        media.download_volume_factor = float(downloadvolumefactor)
        media.seeders = seeders
        # 添加下载
        ret, ret_msg = Downloader().download(media_info=media,
                                             download_dir=dl_dir,
                                             download_setting=dl_setting)
        if ret:
            # 发送消息
            media.user_name = current_user.username
            Message().send_download_message(SearchType.WEB, media)
            return {"code": 0, "msg": "下载成功"}
        else:
            # 发送下载失败通知
            Message().send_download_fail_message(download_item=media, error_msg=ret_msg or "如连接正常，请检查下载任务是否存在")
            return {"code": 1, "msg": ret_msg or "如连接正常，请检查下载任务是否存在"}