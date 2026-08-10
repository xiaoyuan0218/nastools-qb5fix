import json
import requests

from app.message.client._base import _IMessageClient
from app.utils import ExceptionUtils


class Feishu(_IMessageClient):
    schema = "feishu"

    _client_config = {}
    _webhook_url = None
    _sign_check = False
    _sign_secret = None

    def __init__(self, config):
        self._client_config = config
        self.init_config()

    def init_config(self):
        if self._client_config:
            self._webhook_url = self._client_config.get('webhook_url')
            self._sign_check = self._client_config.get('sign_check')
            self._sign_secret = self._client_config.get('sign_secret')

    @classmethod
    def match(cls, ctype):
        return True if ctype == cls.schema else False

    @staticmethod
    def gen_sign(timestamp, secret):
        import hashlib
        import base64
        import hmac
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(hmac_code).decode('utf-8')

    def send_msg(self, title, text="", image="", url="", user_id=""):
        """
        发送飞书消息（Webhook）
        :param title: 消息标题
        :param text: 消息内容
        :param image: 图片地址（飞书Webhook不支持直接发图片，仅附加链接）
        :param url: 点击跳转URL
        :param user_id: Webhook不支持指定用户
        """
        if not title and not text:
            return False, "标题和内容不能同时为空"
        if not self._webhook_url:
            return False, "Webhook 地址未配置"

        try:
            content = f"{title}\n{text}" if text else title
            if url:
                content = f"{content}\n🔗 详情：{url}"
            if image:
                content = f"{content}\n🖼 {image}"

            payload = {
                "msg_type": "text",
                "content": {"text": content}
            }

            if self._sign_check and self._sign_secret:
                import time
                timestamp = str(int(time.time()))
                sign = self.gen_sign(timestamp, self._sign_secret)
                payload["timestamp"] = timestamp
                payload["sign"] = sign

            res = requests.post(
                self._webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            if res and res.status_code == 200:
                ret_json = res.json()
                if ret_json.get("code") == 0:
                    return True, ""
                return False, ret_json.get("msg", "未知错误")
            elif res:
                return False, f"HTTP错误：{res.status_code}"
            return False, "未获取到返回信息"

        except Exception as msg_e:
            ExceptionUtils.exception_traceback(msg_e)
            return False, str(msg_e)

    def send_list_msg(self, medias: list, user_id="", title="", **kwargs):
        """
        发送列表类消息
        :param medias: 媒体列表
        """
        if not medias:
            return False, "参数有误"
        if not self._webhook_url:
            return False, "Webhook 地址未配置"

        try:
            content = f"📋 {title}\n\n"
            for idx, media in enumerate(medias, 1):
                content += f"{idx}. {media.get_title_string()}\n"
                if media.get_vote_string():
                    content += f"   {media.get_type_string()}，{media.get_vote_string()}\n"
                if media.get_detail_url():
                    content += f"   🔗 {media.get_detail_url()}\n"

            payload = {
                "msg_type": "text",
                "content": {"text": content}
            }

            res = requests.post(
                self._webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            if res and res.status_code == 200:
                ret_json = res.json()
                if ret_json.get("code") == 0:
                    return True, ""
                return False, ret_json.get("msg", "未知错误")
            elif res:
                return False, f"HTTP错误：{res.status_code}"
            return False, "未获取到返回信息"

        except Exception as msg_e:
            ExceptionUtils.exception_traceback(msg_e)
            return False, str(msg_e)