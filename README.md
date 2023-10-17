
> 官方网站：https://hexo.io/zh-cn/

## 安装&配置
### 版本升级
```bash
$ npm i hexo-cli -g
$ npm i hexo@5.2.0
```
使用Hexo搭建GitHub博客（2018年Mac版）
https://www.jianshu.com/p/cb0750324e26
https://www.jianshu.com/p/71f58f4b7b30

### 使用next主题
https://www.cnblogs.com/zhangxiaochn/p/Hexo_Theme_Next.html

#### 菜单项设置
https://www.jianshu.com/p/f138032e7539

#### hexo的next主题个性化配置教程
http://shenzekun.cn/hexo%E7%9A%84next%E4%B8%BB%E9%A2%98%E4%B8%AA%E6%80%A7%E5%8C%96%E9%85%8D%E7%BD%AE%E6%95%99%E7%A8%8B.html

### 使用[hexo-theme-butterfly](https://github.com/jerryc127/hexo-theme-butterfly) 主题

```bash
$ npm i hexo-theme-butterfly
$ npm update hexo-theme-butterfly
```
帮助文档：https://butterfly.js.org/posts/21cfbf15/
样例：https://blog.holic-x.com/wv-blog/


## [使用文档](https://hexo.io/docs/)
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
  
### 内容格式化
在线格式化：https://prettier.io/playground/
本地格式化
```
npx prettier . --write ./*.md
```
