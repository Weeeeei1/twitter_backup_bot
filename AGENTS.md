# AGENTS.md - Twitter Backup Bot

## ⚠️ 工作流程规则

**重要！每次部署/修改命令时必须遵循：**

1. **用户提供配置** → 我生成**完整可执行命令** → 用户直接复制到服务器执行
2. **命令分块输出**，每个命令块独立可用，方便用户复制
3. **最后必须输出检查命令**，用于诊断操作是否成功

### 配置提供规则

| 配置项 | 获取方式 | 状态 |
|--------|-----------|------|
| `BOT_TOKEN` | 向 @BotFather 申请 | 用户提供 |
| `ADMIN_TELEGRAM_ID` | 向 @userinfobot 获取 | 用户提供 |
| `Twitter Cookies` | 浏览器登录后 F12 → Application → Cookies | 用户提供 |

### 部署后检查命令

每次部署完成后必须输出：

```bash
# 检查容器状态
docker-compose ps

# 检查 Bot 日志（等待 10 秒后）
sleep 10 && docker-compose logs bot | tail -50
```

---

## 项目概述

Telegram 机器人，用于监控和备份 Twitter/X 推文。

- **架构**: asyncio + python-telegram-bot + twscrape + yt-dlp
- **数据库**: PostgreSQL + Redis
- **多用户隔离**: 私有 Telegram 频道
- **当前版本**: v0.2.0

---

## 服务器部署

### 首次部署

```bash
# 1. 创建目录并克隆
mkdir -p /opt/twitter_backup_bot && cd /opt/twitter_backup_bot && git clone https://github.com/Weeeeei1/twitter_backup_bot.git .
```

```bash
# 2. 创建 .env 文件（用户提供配置后生成完整内容）
cat > /opt/twitter_backup_bot/.env << 'EOF'
BOT_TOKEN=用户提供
ADMIN_TELEGRAM_ID=用户提供
TWITTER_COOKIES=用户提供
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/twitter_backup
REDIS_URL=redis://localhost:6379/0
BASE_CHECK_INTERVAL=300
MIN_CHECK_INTERVAL=60
MAX_CHECK_INTERVAL=3600
LOG_LEVEL=INFO
EOF
```

```bash
# 3. 创建 docker-compose.yml（如需修改）
# 使用项目自带的 docker-compose.yml
```

```bash
# 4. 创建 data 目录并启动
mkdir -p /opt/twitter_backup_bot/data && cd /opt/twitter_backup_bot && docker-compose up -d --build
```

```bash
# 5. 检查命令
docker-compose ps && sleep 10 && docker-compose logs bot | tail -50
```

### 更新代码

```bash
cd /opt/twitter_backup_bot && git pull && docker-compose up -d --build
```

```bash
# 检查命令
docker-compose ps && sleep 10 && docker-compose logs bot | tail -50
```

### 常用命令

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart bot

# 查看状态
docker-compose ps

# 查看所有日志
docker-compose logs -f
```

---

## 配置说明

### 必填配置 (.env)

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `BOT_TOKEN` | Telegram Bot Token (from @BotFather) | `8525071935:AAGZ...` |
| `ADMIN_TELEGRAM_ID` | 管理员 Telegram ID | `123456789` |
| `TWITTER_COOKIES` | Twitter 登录 cookies (JSON 数组) | 见下方详细说明 |

### Twitter Cookies 获取

在浏览器登录 Twitter/X 后，打开开发者工具 (F12) → Application → Cookies → 复制以下字段：
- `auth_token`
- `ct0`
- `twid`
- `guest_id`

```json
[
  {"domain": ".x.com", "name": "auth_token", "value": "..."},
  {"domain": ".x.com", "name": "ct0", "value": "..."},
  {"domain": ".x.com", "name": "twid", "value": "..."},
  {"domain": ".x.com", "name": "guest_id", "value": "..."}
]
```

---

## Bot 命令

| 命令 | 说明 |
|------|------|
| `/start` | 启动机器人，显示版本号 |
| `/help` | 显示帮助信息 |
| `/add_account @用户名` | 添加监控账号 |
| `/list_accounts` | 列出监控账号 |
| `/remove_account @用户名` | 移除监控账号 |
| `/status` | 查看监控状态 |
| `/backup @用户名` | 立即备份推文 |
| `/history @用户名 [时间]` | 获取历史推文 (week/month/3months/year/all) |

---

## 项目结构

```
src/
├── main.py                 # 入口
├── config.py              # 配置管理
├── bot/
│   ├── application.py      # Bot 应用
│   └── handlers/          # 命令处理器
├── db/
│   ├── database.py        # 数据库连接
│   ├── models.py          # SQLAlchemy 模型
│   └── repositories.py   # 数据访问层
├── cache/
│   └── redis.py           # Redis 客户端
├── twitter/
│   ├── client.py          # twscrape 封装
│   ├── parser.py         # 推文解析
│   └── rate_limiter.py    # API 限流
├── media/
│   ├── downloader.py     # yt-dlp 下载
│   └── uploader.py       # Telegram 上传
├── scheduler/
│   ├── adaptive.py        # 动态间隔算法
│   └── pool.py           # 调度池
└── services/
    ├── account_service.py  # 账号管理
    ├── channel_service.py # 频道管理
    └── monitor_service.py # 监控服务
```

---

## 自适应调度算法

检查间隔根据博主发帖频率动态调整：

```
interval = base_interval * (avg_post_interval / base_interval)
interval = max(min_interval, min(max_interval, interval))
```

**默认值**:
- `BASE_CHECK_INTERVAL=300` (5分钟)
- `MIN_CHECK_INTERVAL=60` (1分钟)
- `MAX_CHECK_INTERVAL=3600` (1小时)

---

## 数据库模型

| 模型 | 说明 |
|------|------|
| `User` | Telegram 用户 |
| `TwitterAccount` | 监控的推特账号 |
| `Tweet` | 抓取的推文 |
| `TweetMedia` | 媒体附件 |
| `MonitorStats` | 监控统计 (用于动态间隔) |
| `UserSettings` | 用户设置 |

---

## 注意事项

1. **Twitter Cookies 有效期**: 通常较短，需要定期更新
2. **Bot 权限**: 需要创建私有频道的管理员权限
3. **Rate Limiting**: Twitter 有严格的 API 限流，多账号轮换可提高稳定性
4. **文件限制**: Telegram Bot 最大 50MB 文件，yt-dlp 会自动处理压缩

---

## 开发相关

### 本地运行

```bash
pip install -r requirements.txt
python -m src.main
```

### 运行测试

```bash
pytest tests/ -v
```

### 版本更新

1. 修改 `VERSION` 文件
2. 修改 `src/__init__.py` 中的 `__version__`
3. 修改 `src/config.py` 中的默认值
4. Git commit & push
