# nastools-qb5fix

NAStool v2.9.1 的 qBittorrent 5.2.x 兼容性补丁镜像

## 解决的问题

| 问题 | 原因 | 修复方式 |
|------|------|----------|
| **qB 5.2.x 登录失败** | Cookie 名称从 `SID` 改为 `QBT_SID_{port}` | 修改 `auth.py` 适配新 cookie 名 |
| **添加下载任务失败** | `torrents_add` API 返回 `requests.Response` 对象而非纯文本 `"Ok."` | 使用 `.text` 属性读取响应内容，同时兼容 `"Ok"` 和 `success_count` |
| **下载失败无飞书通知** | Web 下载路由的失败分支未调用通知模块 | 在 `action.py` 的三条下载路由中补充 `send_download_fail_message` 调用 |
| **缺少飞书通知渠道** | NAStool 官方不支持飞书机器人通知 | 新增 `feishu.py` 消息客户端 + `moduleconf.py` 配置项 |
| **飞书通知为纯文本** | 飞书消息仅以 `text` 格式发送 | 升级为 `interactive` 卡片格式，支持标题 emoji、颜色区分、海报链接和详情按钮 |

## 使用方法

### 方式一：从 GitHub 源码构建（推荐）

```bash
git clone https://github.com/xiaoyuan0218/nastools-qb5fix.git
cd nastools-qb5fix
docker build -t nastools-qb5fix:latest .
```

### 方式二：直接拉取预构建镜像

```bash
docker pull ghcr.io/xiaoyuan0218/nastools-qb5fix:latest
```

### Docker Compose 部署

```yaml
services:
  nas-tools:
    image: ghcr.io/xiaoyuan0218/nastools-qb5fix:latest
    restart: always
    ports:
      - 32768:3000
    volumes:
      - ./config:/config
      - /path/to/media:/media
    environment:
      - PUID=0
      - PGID=0
      - TZ=Asia/Shanghai
      - NASTOOL_AUTO_UPDATE=true
```

> **注意**：无需手动指定 `entrypoint`，镜像默认使用修补后的 `/start.sh` 入口，自动在每次启动时应用补丁。

## 补丁持久化机制

NAStool 在启动时执行 `git pull` 更新代码，会重置所有自定义修改。本镜像通过以下机制确保补丁持久化：

1. **层次结构**：补丁文件存储在镜像内的 `/nas-tools-patches/` 目录（Git 仓库之外）
2. **包装入口**：自定义 `/start.sh` 替代官方 `entrypoint.sh`，在每次启动（包括自动更新后）重新应用补丁
3. **覆盖策略**：从 `/nas-tools-patches/` 复制补丁文件覆盖到 `/nas-tools/` 对应位置
4. **重启持久**：`docker restart` 或容器崩溃重启后补丁自动恢复

## 补丁文件说明

| 文件 | 覆盖目标 | 作用 |
|------|---------|------|
| `auth.py` | `third_party/qbittorrent-api/qbittorrentapi/auth.py` | qB 5.2.x cookie 名兼容 |
| `qbittorrent.py` | `app/downloader/client/qbittorrent.py` | `torrents_add` 返回兼容 Response 对象 |
| `feishu.py` | `app/message/client/feishu.py` | 飞书机器人通知客户端 |
| `feishu.png` | `web/static/img/feishu.png` | 飞书图标 |
| `moduleconf.py` | `app/conf/moduleconf.py` | 飞书通知配置项 |
| `action.py` | `web/action.py` | Web 下载失败通知补充 |
| `start.sh` | — | 包装入口脚本，自动应用补丁 |

## 技术栈

- 基础镜像：`ahsyon2023/nastools:db2.9.1`
- 目标平台：qBittorrent 5.2.x
- 通知渠道：飞书机器人 Webhook