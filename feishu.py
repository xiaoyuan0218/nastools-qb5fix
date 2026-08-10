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

    _EMOJI_MAP = {
        "开始下载": "📥",
        "已入库": "✅",
        "已添加订阅": "📌",
        "订阅完成": "🎉",
        "失败": "❌",
        "错误": "⚠️",
        "站点签到": "🔔",
        "站点消息": "📬",
    }
    _COLOR_MAP = {
        "成功": "green",
        "完成": "green",
        "失败": "red",
        "错误": "red",
    }

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

    @staticmethod
    def _choose_emoji(title):
        """根据标题自动匹配 emoji"""
        for keyword, emoji in Feishu._EMOJI_MAP.items():
            if keyword in title:
                return emoji
        return "📢"

    @staticmethod
    def _choose_color(title):
        """根据标题自动匹配颜色"""
        for keyword, color in Feishu._COLOR_MAP.items():
            if keyword in title:
                return color
        return "blue"

    def send_msg(self, title, text="", image="", url="", user_id=""):
        """
        发送飞书消息（卡片格式）
        """
        if not title and not text:
            return False, "标题和内容不能同时为空"
        if not self._webhook_url:
            return False, "Webhook 地址未配置"

        try:
            emoji = self._choose_emoji(title)
            color = self._choose_color(title)

            # 构建卡片 elements
            elements = []

            # 主标题行（如果有 text，把 title 作为 header，text 作为 body）
            if text:
                # 将纯文本中的 \n 转为 lark_md 换行
                md_text = text.replace("\n", "\n")
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": md_text
                    }
                })
            else:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": title
                    }
                })

            # 图片和链接区域
            has_extra = bool(image) or bool(url) or bool(image and url)
            if has_extra:
                elements.append({"tag": "hr"})

            if image:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"🖼 [查看海报]({image})"
                    }
                })

            if url:
                if url == 'downloading':
                    btn_text = "📥 查看下载"
                else:
                    btn_text = "🔗 查看详情"
                elements.append({
                    "tag": "action",
                    "actions": [{
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": btn_text},
                        "url": url,
                        "type": "default"
                    }]
                })

            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": f"{emoji} {title.split(chr(10))[0]}"
                        },
                        "template": color
                    },
                    "elements": elements
                }
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
        发送列表类消息（卡片格式）
        """
        if not medias:
            return False, "参数有误"
        if not self._webhook_url:
            return False, "Webhook 地址未配置"

        try:
            elements = [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"📋 **{title or '列表'}**"
                    }
                },
                {"tag": "hr"}
            ]

            for idx, media in enumerate(medias, 1):
                line = f"{idx}. **{media.get_title_string()}**"
                if media.get_vote_string():
                    line += f"\n   {media.get_type_string()}，{media.get_vote_string()}"
                if media.get_detail_url():
                    line += f"\n   🔗 {media.get_detail_url()}"
                elements.append({
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": line}
                })

            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": f"📋 {title or '列表'}"
                        },
                        "template": "blue"
                    },
                    "elements": elements
                }
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