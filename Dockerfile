FROM ahsyon2023/nastools:db2.9.1

# ==============================================================
# qB5fix + Feishu notification patches for NAStool
# ==============================================================
# Patches are stored in /nas-tools-patches/ and applied at startup
# by the wrapper entrypoint (start.sh), which runs AFTER git reset
# to ensure patches survive auto-update.

# qBittorrent 5.2.x cookie name fix (SID -> QBT_SID_8080)
COPY auth.py /nas-tools-patches/third_party/qbittorrent-api/qbittorrentapi/auth.py

# Feishu (飞书) notification client
COPY feishu.py /nas-tools-patches/app/message/client/feishu.py
COPY feishu.png /nas-tools-patches/web/static/img/feishu.png
COPY moduleconf.py /nas-tools-patches/app/conf/moduleconf.py

# Fix: send_download_fail_message on download failure (web action route)
COPY action.py /nas-tools-patches/web/action.py

# Fix: qB 5.2.x JSON response format (qB 5.x returns {"success_count":1,...} instead of "Ok.")
COPY qbittorrent.py /nas-tools-patches/app/downloader/client/qbittorrent.py

# Wrapper entrypoint (outside repo, survives git reset)
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Keep original entrypoint for reference
COPY entrypoint.sh /nas-tools/docker/entrypoint.sh
RUN chmod +x /nas-tools/docker/entrypoint.sh

# Override ENTRYPOINT to use wrapper
ENTRYPOINT ["/start.sh"]