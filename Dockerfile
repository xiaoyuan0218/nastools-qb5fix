FROM ahsyon2023/nastools:db2.9.1

# qBittorrent 5.2.x cookie name fix (SID -> QBT_SID_8080)
# Copy to patches dir so entrypoint can restore it after git reset
COPY auth.py /nas-tools-patches/third_party/qbittorrent-api/qbittorrentapi/auth.py
COPY feishu.py /nas-tools-patches/app/message/client/feishu.py
COPY feishu.png /nas-tools-patches/web/static/img/feishu.png
COPY moduleconf.py /nas-tools-patches/app/conf/moduleconf.py

# Patched entrypoint that restores custom files after git reset
COPY entrypoint.sh /nas-tools/docker/entrypoint.sh
RUN chmod +x /nas-tools/docker/entrypoint.sh