#!/bin/sh

cd ${WORKDIR}
if [ "${NASTOOL_AUTO_UPDATE}" = "true" ]; then
    # ... (原有依赖检查逻辑保持不变)

    echo "更新程序..."
    git remote set-url origin "${REPO_URL}" &> /dev/null
    echo "windows/" > .gitignore
    if [ "${NASTOOL_VERSION}" == "dev" ]; then
      branch="dev"
    else
      branch="master"
    fi
    git clean -dffx
    git fetch --depth 1 origin ${branch}
    git reset --hard origin/${branch}
    if [ $? -eq 0 ]; then
        echo "更新成功..."

        # ===== 恢复自定义补丁文件 (qb5fix + feishu) =====
        if [ -d /nas-tools-patches/app ]; then
            echo "正在应用自定义补丁..."
            cp -rf /nas-tools-patches/app/message/client/feishu.py /nas-tools/app/message/client/feishu.py 2>/dev/null
            cp -rf /nas-tools-patches/web/static/img/feishu.png /nas-tools/web/static/img/feishu.png 2>/dev/null
            cp -rf /nas-tools-patches/app/conf/moduleconf.py /nas-tools/app/conf/moduleconf.py 2>/dev/null
            cp -rf /nas-tools-patches/third_party/qbittorrent-api/qbittorrentapi/auth.py /nas-tools/third_party/qbittorrent-api/qbittorrentapi/auth.py 2>/dev/null
            echo "补丁应用完成"
        fi
        # ===== 恢复结束 =====

        # Python依赖包更新
        # ... (后续逻辑保持不变)