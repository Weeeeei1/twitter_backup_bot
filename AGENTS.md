# AGENTS.md - Twitter Backup Bot

## ⚠️ 工作流程规则

**重要！每次部署/修改命令时必须遵循：**

1. **用户提供配置** → 我生成**完整可执行命令** → 用户直接复制到服务器执行
2. **命令分块输出**，每个命令块独立可用，方便用户复制
3. **最后必须输出检查命令**，用于诊断操作是否成功

### 部署后检查命令

```bash
docker-compose ps
docker-compose logs -f bot
```

---

## 项目概述

Telegram 机器人，用于监控和备份 Twitter/X 推文。

- **架构**: asyncio + python-telegram-bot + twscrape + yt-dlp
- **数据库**: PostgreSQL + Redis
- **多用户隔离**: 私有 Telegram 频道
- **当前版本**: v0.2.1
- **入口**: `src/main.py`

---

## ⚠️ 调试经验总结（重要！）

### 1. Handler 必须注册
每个 handler 函数必须在 `application.py` 的 `_register_handlers()` 中注册：
```python
from src.bot.handlers.status import status_handler  # 必须导入
self.app.add_handler(CommandHandler("status", status_handler))  # 必须注册
```

### 2. 版本号从 VERSION 文件读取
`config.py` 的 `_get_version_from_file()` 从 `VERSION` 文件读取，**不要硬编码**：
```bash
# 更新版本号需要修改：
# 1. VERSION 文件
# 2. src/__init__.py 的 __version__
```

### 3. twscrape 返回 async generator
`api.user_tweets()` 返回 **async generator**，必须用 `async for` 遍历：
```python
# 错误：
tweets = await self.api.user_tweets(username, limit=100)
# 正确：
async for tweet in self.api.user_tweets(username, limit=100):
    ...
```

### 4. 共享状态通过 state.py
Handler 之间共享状态使用 `src.bot.state` 模块：
```python
from src.bot import state as state_module
state_module.account_service = account_service  # 设置
state_module.account_service.get_account_stats()  # 获取
```

### 5. Repository 方法缺失问题
如果遇到 `'XXXRepository' object has no attribute 'yyy'` 错误，需要在 `src/db/repositories.py` 中添加对应方法。

---

## 服务器部署

### 更新代码

```bash
cd /opt/twitter_backup_bot && git fetch origin && git reset --hard origin/main && docker-compose up -d --build
```

### 常用命令

```bash
docker-compose ps                    # 查看状态
docker-compose logs -f bot           # 实时日志
docker-compose restart bot           # 重启 Bot
docker-compose down                  # 停止
```

---

## 项目结构

```
src/
├── main.py                 # 入口
├── config.py               # 配置管理（从 VERSION 文件读取版本）
├── __init__.py            # 版本号定义
├── bot/
│   ├── application.py     # Bot 应用（所有 handler 在此注册）
│   ├── state.py           # 共享状态模块
│   ├── menus/             # 按钮菜单
│   └── handlers/          # 命令处理器
├── db/
│   ├── database.py        # 数据库连接
│   ├── models.py          # SQLAlchemy 模型
│   └── repositories.py    # 数据访问层
├── cache/
│   └── redis.py           # Redis 客户端
├── twitter/
│   └── client.py          # twscrape 封装（使用 async for）
├── scheduler/
│   └── pool.py           # 调度池（包含 trigger_immediate_check）
└── services/
    ├── account_service.py  # 账号管理
    └── monitor_service.py # 监控服务
```

---

## 配置说明

### 必填配置 (.env)

| 配置项 | 说明 |
|--------|------|
| `BOT_TOKEN` | Telegram Bot Token (from @BotFather) |
| `ADMIN_TELEGRAM_ID` | 管理员 Telegram ID |
| `TWITTER_COOKIES` | Twitter 登录 cookies (JSON 数组) |

### Twitter Cookies 获取

浏览器登录 Twitter/X 后，F12 → Application → Cookies：
- `auth_token`
- `ct0`

---

## 代码修改流程

1. 本地修改代码
2. 推送到 GitHub
3. 服务器执行：`git fetch origin && git reset --hard origin/main && docker-compose up -d --build`

**禁止在服务器上直接修改代码！**

---

## 开发相关

### 本地运行

```bash
pip install -r requirements.txt
python -m src.main
```

### 版本更新

1. 修改 `VERSION` 文件
2. 修改 `src/__init__.py` 的 `__version__`
3. Git commit & push

---

## 已知问题

### Twitter 限流
twscrape 使用模拟登录+网页请求，Twitter 会通过 IP + 请求频率检测机器人。单账号 cookies 容易被限流。

**解决方案**：
1. 使用多账号 cookies 轮换
2. 降低检查频率（增大 `BASE_CHECK_INTERVAL`）
3. 使用代理 IP
