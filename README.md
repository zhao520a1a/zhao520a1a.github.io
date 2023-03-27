
> 官方网站：https://hexo.io/zh-cn/

## 版本升级
```bash
$ npm i hexo-cli -g
$ npm i hexo@5.2.0
```

### [hexo-theme-butterfly](https://github.com/jerryc127/hexo-theme-butterfly) 主题

```bash
$ npm i hexo-theme-butterfly
$ npm update hexo-theme-butterfly
```

帮助文档：https://butterfly.js.org/posts/21cfbf15/

## 帮助文档

https://hexo.io/docs/

### 创建文章

``` bash
$ hexo new "My New Post"
```

More info: [Writing](https://hexo.io/docs/writing.html)

### 本地启动

``` bash
$ hexo server
```

More info: [Server](https://hexo.io/docs/server.html)

###  生成静态文档

``` bash
$ hexo generate
```

More info: [Generating](https://hexo.io/docs/generating.html)

### 发布到远程

``` bash
$ hexo deploy
```

More info: [Deployment](https://hexo.io/docs/one-command-deployment.html)

### 生成并发布：
``` bash
$ hexo g -d
```

### 组合命令
``` bash
hexo clean && hexo g && hexo d
```



## 文章撰写



### 文章分类
开发工具 
数据存储 
架构设计 
源码解读 
编码规范 

```markdown
---
tags: [go]   
categories: [源码解读]
---
```
### 内容格式化
在线格式化
https://prettier.io/playground/

本地格式化
```
 prettier --write ./*.md
```
