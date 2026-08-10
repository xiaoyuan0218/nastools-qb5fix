FROM ahsyon2023/nastools:db2.9.1

# qBittorrent 5.2.x cookie name fix (SID -> QBT_SID_8080)
COPY auth.py /nas-tools/third_party/qbittorrent-api/qbittorrentapi/auth.py

# Feishu (Lark) Webhook notification client
COPY feishu.py /nas-tools/app/message/client/feishu.py
COPY feishu.png /nas-tools/web/static/img/feishu.png
COPY moduleconf.py /nas-tools/app/conf/moduleconf.py