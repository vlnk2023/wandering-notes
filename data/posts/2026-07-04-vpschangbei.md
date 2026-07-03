---
title: "VPS常用命令"
date: 2026-07-04
tags: [VPS]
summary: >-
  VPS命令简介
---

用户权限与管理

作用：切换到 root 用户，并保持 root 环境变量
命令：sudo -i

作用：切换到 root 用户，保持完整环境
命令：sudo su -

作用：以 root 权限执行命令
命令：sudo <command>

作用：显示当前用户名
命令：whoami

作用：查看当前用户 ID 和组信息
命令：id

作用：显示当前用户所属组
命令：groups

作用：修改当前用户密码
命令：passwd

作用：新增用户
命令：adduser <username>

作用：删除用户及家目录
命令：userdel -r <username>

作用：将用户添加到组
命令：usermod -aG <group> <user>

作用：查看当前用户登录信息
命令：w

作用：查看最近登录用户
命令：last

作用：锁定用户
命令：usermod -L <username>

作用：解锁用户
命令：usermod -U <username>

作用：切换用户
命令：su - <username>

系统信息

作用：查看系统内核信息
命令：uname -a

作用：查看操作系统版本
命令：cat /etc/os-release

作用：查看系统运行时间和负载
命令：uptime

作用：查看主机名
命令：hostname

作用：查看磁盘空间使用情况
命令：df -h

作用：查看指定目录大小
命令：du -sh <folder>

作用：查看内存使用情况
命令：free -h

作用：实时查看进程、CPU、内存占用
命令：top

作用：增强版 top，需要安装
命令：htop

作用：查看系统最近启动日志
命令：dmesg | tail -n 50

作用：查看 CPU 信息
命令：lscpu

作用：查看硬盘信息
命令：lsblk

作用：查看内核模块
命令：lsmod

作用：查看系统时间
命令：date

作用：查看时区信息
命令：timedatectl

作用：查看开机时间
命令：who -b

文件与目录操作

作用：列出目录内容，带大小和可读格式
命令：ls -lh

作用：切换目录
命令：cd /path

作用：显示当前目录路径
命令：pwd

作用：创建目录（包含上级目录）
命令：mkdir -p <dir>

作用：强制删除目录及其内容
命令：rm -rf <dir>

作用：复制文件或目录
命令：cp -r <src> <dest>

作用：移动或重命名文件或目录
命令：mv <src> <dest>

作用：新建空文件
命令：touch <file>

作用：查看文件内容
命令：cat <file>

作用：分页查看文件内容
命令：less <file>

作用：查看文件前 20 行
命令：head -n 20 <file>

作用：查看文件后 20 行
命令：tail -n 20 <file>

作用：按名称查找文件
命令：find /path -name "<pattern>"

作用：文件内容搜索
命令：grep "pattern" <file>

作用：比较两个文件内容
命令：diff <file1> <file2>

作用：显示文件前 100 行
命令：head -n 100 <file>

作用：显示文件后 100 行
命令：tail -n 100 <file>

作用：复制文件内容到剪贴板（Linux xclip）
命令：xclip -sel clip < file>

网络与端口

作用：测试目标主机连通性
命令：ping <host>

作用：查看 HTTP 响应头
命令：curl -I <url>

作用：下载文件
命令：wget <url>

作用：查看网络连接和端口占用
命令：netstat -tulnp

作用：查看网络连接和端口占用（替代 netstat）
命令：ss -tulnp

作用：路由追踪
命令：traceroute <host>

作用：DNS 查询
命令：dig <domain>

作用：查看网络接口信息
命令：ifconfig 或 ip addr

作用：查看公网 IP
命令：curl ifconfig.me

作用：远程拷贝文件
命令：scp <file> user@host:/path

作用：远程同步文件
命令：rsync -avz <src> user@host:/path

作用：测试端口是否开放
命令：nc -zv <host> <port>

作用：测试端口连接
命令：telnet <host> <port>

软件管理（Debian/Ubuntu）

作用：更新软件源列表
命令：apt update

作用：升级所有软件包
命令：apt upgrade -y

作用：安装软件
命令：apt install <package>

作用：卸载软件
命令：apt remove <package>

作用：自动删除无用依赖
命令：apt autoremove -y

作用：查看已安装软件包
命令：dpkg -l

作用：搜索软件包
命令：apt search <package>

作用：查看软件包信息
命令：apt show <package>

软件管理（CentOS/RHEL）

作用：更新软件包
命令：yum update -y

作用：安装软件
命令：yum install <package>

作用：卸载软件
命令：yum remove <package>

作用：查看已安装软件包
命令：rpm -qa

作用：搜索软件包
命令：yum search <package>

作用：查看软件包信息
命令：yum info <package>

服务与进程

作用：查看服务状态
命令：systemctl status <service>

作用：启动服务
命令：systemctl start <service>

作用：停止服务
命令：systemctl stop <service>

作用：重启服务
命令：systemctl restart <service>

作用：开机启动服务
命令：systemctl enable <service>

作用：取消开机启动服务
命令：systemctl disable <service>

作用：查看当前运行的进程
命令：ps aux

作用：实时监控进程
命令：top

作用：增强版 top
命令：htop

作用：杀掉指定进程
命令：kill <PID>

作用：强制杀掉进程
命令：kill -9 <PID>

作用：按进程名杀掉进程
命令：pkill <process>

压缩与解压

作用：压缩目录成 tar.gz
命令：tar -czvf file.tar.gz folder/

作用：解压 tar.gz 文件
命令：tar -xzvf file.tar.gz

作用：解压 tar.bz2 文件
命令：tar -xjvf file.tar.bz2

作用：压缩成 zip
命令：zip -r file.zip folder/

作用：解压 zip 文件
命令：unzip file.zip

日志与监控

作用：查看系统日志
命令：journalctl -xe

作用：实时跟踪日志
命令：tail -f /var/log/syslog

作用：实时跟踪日志（CentOS）
命令：tail -f /var/log/messages

作用：每 5 秒刷新运行命令结果
命令：watch -n 5 'command'

作用：查看磁盘 I/O 状况
命令：iostat

作用：实时查看内存和 CPU
命令：vmstat 5

网络调试

作用：连续 traceroute + ping
命令：mtr <host>

作用：启动带宽测试服务器
命令：iperf3 -s

作用：带宽测试客户端
命令：iperf3 -c <server>

作用：测试端口是否开放
命令：nc -zv <host> <port>

作用：端口连接测试
命令：telnet <host> <port>

计划任务与定时

作用：编辑当前用户定时任务
命令：crontab -e

作用：查看定时任务
命令：crontab -l

作用：查看系统定时器
命令：systemctl list-timers

磁盘与分区管理

作用：列出磁盘与分区
命令：lsblk

作用：查看磁盘分区表
命令：fdisk -l

作用：挂载分区
命令：mount /dev/sda1 /mnt

作用：卸载分区
命令：umount /mnt

作用：查看磁盘使用情况
命令：df -h

作用：查看目录大小
命令：du -sh /path

其他常用

作用：查看系统时间
命令：date

作用：管理时间和时区
命令：timedatectl

作用：查看环境变量 PATH
命令：echo $PATH

作用：设置环境变量
命令：export VAR=value

作用：查看历史命令
命令：history

作用：定义命令别名
命令：alias ll='ls -lh'
