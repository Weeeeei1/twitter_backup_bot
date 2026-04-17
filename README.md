# Twitter Backup Bot

Telegram 机器人 - 监控和备份 Twitter 推文

## 功能

- 监控 Twitter 博主新帖子
- 自适应检查间隔（高频博主缩短间隔，低频博主延长间隔）
- 备份推文、线程、图片、视频、GIF
- 上传到 Telegram 私有频道
- 多用户隔离

## 版本

当前版本: **v0.1.0**

## 部署

```bash
# 拉取代码
git pull origin main

# 使用 Docker 启动
docker-compose up -d
```

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python -m src.main
```
