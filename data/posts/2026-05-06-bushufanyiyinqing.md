---
title: 在 Windows 11 的 WSL2 中部署 LibreTranslate
date: 2026-05-06
tags: [技术笔记]
summary: "在 Windows 11 的 WSL2 中部署 LibreTranslate"
---

在 Windows 11 的 WSL2 中部署 LibreTranslate，最推荐的方式是结合 **Docker Desktop**。这样你可以利用 WSL2 的 Linux 内核性能，同时通过 Windows 界面方便地管理资源。

以下是具体的部署步骤：

## 1. 环境准备 (Windows 端)

- **安装 WSL2**: 打开 PowerShell (管理员)，运行 `wsl --install`。如果已安装，请确保它是版本 2。
- **安装 Docker Desktop**: 从 [Docker 官网](https://www.docker.com/products/docker-desktop/)下载并安装。
  - 在安装过程中，务必勾选 **"Use the WSL 2 based engine"**。
  - 安装完成后，进入 Docker 设置 `Settings > Resources > WSL Integration`，勾选你正在使用的 Linux 分发版（如 Ubuntu）以开启集成。

## 2. 在 WSL2 中部署 (Linux 终端)

打开你的 WSL 终端（如 Ubuntu），执行以下操作：

### 方法 A：快速运行 (适合测试)

直接通过 Docker 命令拉取并运行容器：

```bash
docker run -ti --rm -p 5000:5000 libretranslate/libretranslate
```

- 首次运行会下载数 GB 的语言模型，请耐心等待。
- 完成后访问浏览器：`http://localhost:5000`。

### 方法 B：使用 Docker Compose (推荐，适合长期自托管)

使用 Docker Compose 部署可以更好地管理数据卷，实现语言模型的持久化，避免容器重启导致重新下载。

1. **项目设置**: 创建目录并新建 `docker-compose.yml` 文件。建议使用 `volumes` 将语言模型持久化，以避免每次重启容器都重新下载。
2. **启动服务**: 使用 `docker compose up -d` 在后台运行。


