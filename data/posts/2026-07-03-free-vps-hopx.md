---
title: "德国免费VPS部署临时节点"
date: 2026-07-03
tags: [代理节点]
summary: >-
  部署免费代理
---


# 前置准备

需要准备：

```text
1. HopX 账号和 API Key
2. Cloudflare 账号
3. 已托管到 Cloudflare 的域名，例如 phyu.de5.net
4. Cloudflare Tunnel Token
5. 两个子域名：
   - hopx.phyu.de5.net
   - proxy2.phyu.de5.net
```

# Cloudflare Tunnel 控制台配置

进入 Cloudflare Zero Trust：

```text
Zero Trust → Networks → Tunnels → 你的 Tunnel → Public Hostnames
```

添加两条 Public Hostname。

## 1. 面板入口

```text
Subdomain / Hostname: hopx.phyu.de5.net
Path: 留空
Type: HTTP
URL: http://localhost:2053
```

注意：`Path` 必须留空。

不要写：

```text
/panel-1111
```

也不要把 Service 写成：

```text
http://localhost:2053/panel-1111
```

正确是：

```text
http://localhost:2053
```

浏览器访问时才带路径：

```text
https://hopx.phyu.de5.net/panel-1111/
```

## 2. 节点入口

```text
Subdomain / Hostname: proxy2.phyu.de5.net
Path: 留空
Type: HTTP
URL: http://localhost:10000
```

同样，`Path` 留空。
# 开始部署


 https://console.hopx.dev/overview 申请账号登陆后，申请API KEY，然后打开 https://ssh.cloud.google.com/  打开这个终端，输入：

```
hopx_live_dSAs1jBQM0i9.E0m2VYJX9RKv_RUdG2qhMOFeT6yrp8tPcxcgPiZsaDE   需要重新替换


rm -rf hopx2vps

git clone https://github.com/vlnk2023/hopx2vps.git
cd hopx2vps
apt install -y python3-pip
pip install hopx-ai 
python3 run.py

```
  

菜单里选择：

```text
12) 一键部署 3x-ui:2053 + Cloudflare Tunnel Token
```

部署时填写：

```text
面板用户名：mingming2 或自定义
面板密码：强密码
面板端口：2053
面板路径：/panel-1111
面板域名：hopx.phyu.de5.net
Cloudflare Tunnel Token：粘贴完整 token
```

部署完成后，3x-ui 正常情况下会显示类似：

```text
Port:        2053
WebBasePath: /panel-1111
Access URL: http://xxx.xxx.xxx.xxx:2053//panel-1111
```

 

cloudflared tunnel的设置，要在同一个tunnel下，

```
面板域名：hopx.phyu.de5.net → http://localhost:2053
节点域名：proxy2.phyu.de5.net → http://localhost:10000
```

cloudflared tunnel run --token eyJhIjoiMWMxNTYzY2E3M2M1OWQzZWJiYWFiYWI5NGJmMDE4MzAiLCJ0IjoiMTM0N2ZkMDMtYzMwOS00MjI0LThjZTUtZGFmMTEyMWY0Y2RlIiwicyI6IlpEWTBNREUxT1RrdFpUZzJZaTAwTmpoaExUazJabUl0T1RrMlpUWmtOVGRrTmpObCJ9

user mingming2
thub@user#conten23

/panel-1111
修改为2053端口

hopx.phyu.de5.net

proxy2.phyu.de5.net


# 启动 cloudflared tunnel

HopX 沙盒里后台启动 `cloudflared` 不稳定，有时会触发资源限制。

最稳的方式是前台启动：

```bash
cloudflared tunnel --no-autoupdate --loglevel info run --token '你的CloudflareTunnelToken'

## 需要替换一下
```

让 Tunnel 已经连上 Cloudflare。这个命令会一直占着终端，这是正常的，因为 `cloudflared` 是 Tunnel 常驻进程。不要关掉这个终端。
 
# 创建 VLESS WebSocket 入站

登录：

```text
https://hopx.phyu.de5.net/panel-1111/
```

进入：

```text
Inbounds / 入站列表 → Add Inbound / 添加入站
```

## Basics

填写：

```text
Protocol: VLESS
Remark: vless-ws-cf
Listen IP: 127.0.0.1
Port: 10000
```

解释：

```text
2053 是 3x-ui 面板端口
10000 是 Xray/VLESS 本地入站端口
443 是客户端连接 Cloudflare 的端口
```

## Stream

在 `Transmission` 里选择：

```text
WebSocket
Host: proxy2.phyu.de5.net
Path: /vlessws-a8f3k2
```


## Security

填写：

```text
Security: none
```

不要在 3x-ui 入站里开 TLS，也不要开 Reality。

原因是：

```text
客户端 → Cloudflare 这一段由 Cloudflare 提供 TLS
Cloudflare Tunnel → localhost:10000 这一段走本地 HTTP/WebSocket
```

Sniff开启，HTTPX 和TLSX两个
## Client

填写：

```text
UUID: 自动生成
Email: 任意标识，例如 user1
Flow: 留空
Encryption: none
Attached inbounds：vless-ws-cf
```

VLESS 不要填 VMess 那种加密方式。


# 检查 VLESS 入站是否监听

创建入站后，在 HopX 终端执行：

```bash
ss -lntp | grep ':10000'
```

你成功时看到的是：

```text
LISTEN 0 4096 127.0.0.1:10000 0.0.0.0:* users:(("xray-linux-amd64",pid=...,fd=...))
```

这说明 Xray 已经监听了本地 `10000` 端口。

然后测试 Cloudflare 节点入口：

```bash
curl -I https://proxy2.phyu.de5.net/vlessws-a8f3k2
```

成功时你看到：

```text
HTTP/2 400
sec-websocket-version: 13
server: cloudflare
```

这就是正确现象。普通 `curl -I` 不是 WebSocket/VLESS 客户端，所以返回 `400` 很正常；关键是已经不是 `530` 或 `1033`。

# 客户端配置

客户端类型选：

```text
VLESS
```

参数填写：

```text
Address / 地址: proxy2.phyu.de5.net
Port / 端口: 443
UUID: 3x-ui 里生成的 UUID
Encryption / 加密: none
Flow: 留空
Transport / 传输: WebSocket / ws
Path: /vlessws-a8f3k2
Host: proxy2.phyu.de5.net
TLS: 开启
SNI / Server Name: proxy2.phyu.de5.net
Fingerprint: chrome
```

最终客户端配置表：

|项目|值|
|---|---|
|协议|VLESS|
|地址|`proxy2.phyu.de5.net`|
|端口|`443`|
|UUID|3x-ui 生成|
|加密|`none`|
|Flow|留空|
|传输|WebSocket|
|Path|`/vlessws-a8f3k2`|
|Host|`proxy2.phyu.de5.net`|
|TLS|开启|
|SNI|`proxy2.phyu.de5.net`|
|Fingerprint|`chrome`|

