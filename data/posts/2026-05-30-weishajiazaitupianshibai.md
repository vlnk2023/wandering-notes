---
title: github图片为啥加载失败
date: 2026-05-30
tags: [技术笔记]
summary: "本站笔记中图片加载无效怎么办"
---

## 正文

浏览器的 `<img>` 需要拿到 `image/png`，但现在拿到的是 HTML 页面，所以图片加载无效。

我测试了正确 raw 直链，是可用的：

```text
https://raw.githubusercontent.com/vlnk2023/wandering-notes/main/data/posts/image.png
```
 

**修复方式：**

把 Markdown 里的图片链接从：

```md
![](https://github.com/vlnk2023/wandering-notes/blob/main/data/posts/image.png)
```

改成：

```md
![](https://raw.githubusercontent.com/vlnk2023/wandering-notes/main/data/posts/image.png)
```

更推荐的长期做法是把图片放到站点 `public` 目录，例如：

```text
public/images/posts/weishenmejiangdaoliwuxiao.png
```

然后文章里写：

```md
![为什么讲道理无效](/images/posts/weishenmejiangdaoliwuxiao.png)
```

这样部署后图片由你自己的网站提供，不依赖 GitHub raw，也更稳定。当前失效的根因就是：用了 GitHub `blob` 页面地址当图片地址。
