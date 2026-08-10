#!/bin/sh
set -e

# ==============================================================
# NAStool qB5fix + Feishu Patches — Wrapper Entrypoint
# ==============================================================
# This wrapper ensures custom patches survive git reset --hard.
# It lives at /start.sh (container root, outside the repo) so it
# is NOT affected by git operations on /nas-tools/.

WORKDIR=${WORKDIR:-/nas-tools}
cd ${WORKDIR}

# ------------------------------------------------------------------
# Phase 1: Auto-update (with patch survival)
# ------------------------------------------------------------------
if [ "${NASTOOL_AUTO_UPDATE}" = "true" ]; then
    echo "【qb5fix】执行自动更新..."

    # Init hash tracking files if missing
    if [ ! -s /tmp/requirements.txt.sha256sum ] && [ -f requirements.txt ]; then
        sha256sum requirements.txt > /tmp/requirements.txt.sha256sum 2>/dev/null || true
    fi
    if [ ! -s /tmp/third_party.txt.sha256sum ] && [ -f third_party.txt ]; then
        sha256sum third_party.txt > /tmp/third_party.txt.sha256sum 2>/dev/null || true
    fi
    if [ ! -s /tmp/package_list.txt.sha256sum ] && [ -f package_list.txt ]; then
        sha256sum package_list.txt > /tmp/package_list.txt.sha256sum 2>/dev/null || true
    fi

    # Save original .gitignore
    ORIG_GITIGNORE=""
    [ -f .gitignore ] && ORIG_GITIGNORE=$(cat .gitignore)

    git remote set-url origin "${REPO_URL}" &> /dev/null
    echo "windows/" > .gitignore
    git clean -dffx
    git fetch --depth 1 origin ${NASTOOL_VERSION:-master}
    git reset --hard origin/${NASTOOL_VERSION:-master}
    UPD_OK=$?

    # Restore .gitignore (add windows/ back)
    echo "windows/" > .gitignore

    if [ $UPD_OK -eq 0 ]; then
        echo "更新成功..."

        # === Python deps update check ===
        hash_old=$(cat /tmp/requirements.txt.sha256sum 2>/dev/null || echo "")
        hash_new=$(sha256sum requirements.txt 2>/dev/null || echo "")
        if [ "${hash_old}" != "${hash_new}" ] && [ -n "${hash_new}" ]; then
            echo "检测到requirements.txt有变化，重新安装依赖..."
            if [ "${NASTOOL_CN_UPDATE}" = "true" ]; then
                pip install --upgrade pip setuptools wheel -i "${PYPI_MIRROR}" 2>/dev/null || true
                pip install -r requirements.txt -i "${PYPI_MIRROR}" 2>/dev/null || true
            else
                pip install --upgrade pip setuptools wheel 2>/dev/null || true
                pip install -r requirements.txt 2>/dev/null || true
            fi
            sha256sum requirements.txt > /tmp/requirements.txt.sha256sum 2>/dev/null || true
        fi

        # === Third-party submodules update check ===
        hash_old=$(cat /tmp/third_party.txt.sha256sum 2>/dev/null || echo "")
        hash_new=$(sha256sum third_party.txt 2>/dev/null || echo "")
        if [ "${hash_old}" != "${hash_new}" ] && [ -n "${hash_new}" ]; then
            echo "检测到third_party.txt有变化，更新第三方组件..."
            git submodule update --init --recursive 2>/dev/null || true
            sha256sum third_party.txt > /tmp/third_party.txt.sha256sum 2>/dev/null || true
        fi

        # === System packages update check ===
        hash_old=$(cat /tmp/package_list.txt.sha256sum 2>/dev/null || echo "")
        hash_new=$(sha256sum package_list.txt 2>/dev/null || echo "")
        if [ "${hash_old}" != "${hash_new}" ] && [ -n "${hash_new}" ]; then
            echo "检测到package_list.txt有变化，更新软件包..."
            if [ "${NASTOOL_CN_UPDATE}" = "true" ]; then
                sed -i "s/dl-cdn.alpinelinux.org/${ALPINE_MIRROR}/g" /etc/apk/repositories 2>/dev/null || true
                apk update -f 2>/dev/null || true
            fi
            apk add --no-cache $(echo $(cat package_list.txt)) 2>/dev/null || true
            sha256sum package_list.txt > /tmp/package_list.txt.sha256sum 2>/dev/null || true
        fi
    else
        echo "更新失败，继续使用旧版本..."
    fi
fi

# ------------------------------------------------------------------
# Phase 2: Apply custom patches (always, even without auto-update)
# ------------------------------------------------------------------
if [ -d /nas-tools-patches ]; then
    echo "正在应用自定义补丁..."
    cp -f /nas-tools-patches/app/message/client/feishu.py /nas-tools/app/message/client/feishu.py 2>/dev/null || true
    cp -f /nas-tools-patches/web/static/img/feishu.png /nas-tools/web/static/img/feishu.png 2>/dev/null || true
    cp -f /nas-tools-patches/app/conf/moduleconf.py /nas-tools/app/conf/moduleconf.py 2>/dev/null || true
    cp -f /nas-tools-patches/app/web/action.py /nas-tools/app/web/action.py 2>/dev/null || true
    cp -f /nas-tools-patches/third_party/qbittorrent-api/qbittorrentapi/auth.py /nas-tools/third_party/qbittorrent-api/qbittorrentapi/auth.py 2>/dev/null || true
    echo "补丁应用完成"
fi

# ------------------------------------------------------------------
# Phase 3: Start the app
# ------------------------------------------------------------------
echo "以 PUID=${PUID:-0}，PGID=${PGID:-0} 的身份启动程序..."

mkdir -p /.local /.pm2
chown -R "${PUID:-0}":"${PGID:-0}" "${WORKDIR}" /config /usr/lib/chromium /.local /.pm2 2>/dev/null || true
export PATH=${PATH}:/usr/lib/chromium

umask "${UMASK:-022}"
exec su-exec "${PUID:-0}":"${PGID:-0}" "$(which dumb-init)" "$(which pm2-runtime)" start run.py -n NAStool --interpreter python3