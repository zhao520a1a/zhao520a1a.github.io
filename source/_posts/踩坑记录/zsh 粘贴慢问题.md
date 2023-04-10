---
title: zsh 粘贴慢问题
tags: [zsh]
categories: [效率工具]
date: 2021-08-20
cover: https://github.com/zhao520a1a/zhao520a1a.github.io/blob/hexo/source/cover/zsh.png?raw=true
---

### 安装 iTerm2
关于iTerm2 你不知道的一些事：
- [iTerm2 + Oh My Zsh 打造舒适终端体验](https://segmentfault.com/a/1190000014992947)

- [关于iTerm2 你不知道的一些事](https://www.jianshu.com/p/3436bcb17a03)


### 问题描述
使用 iTerm2 终端每次在粘贴大量命令的时间，明显感觉粘贴速度慢。就感觉粘贴也是一个字一个字粘贴的。在命令过长时由为明显。根本原因是由zsh-autosuggestions插件引起的。官方指引：[Maybe fix for slow pastes ](https://github.com/zsh-users/zsh-autosuggestions/issues/238)

### 解决方案
编辑 ~/.zshrc并增加以下代码

``` bash
pasteinit() {
  OLD_SELF_INSERT=${${(s.:.)widgets[self-insert]}[2,3]}
  zle -N self-insert url-quote-magic 
}

pastefinish() {
  zle -N self-insert $OLD_SELF_INSERT
}
zstyle :bracketed-paste-magic paste-init pasteinit
zstyle :bracketed-paste-magic paste-finish pastefinish
```

使用代码生效
```
source ~/.zshrc
```

### 参考：

[zsh 粘贴加速，解决粘贴卡慢问题](https://www.jianshu.com/p/83d9b8e245ae)