---
title: shell实现SSH自动登陆
tags: [zsh]
categories: [开发工具]
---

[TOC]

> 作为一个工具人，时刻保持着`偷懒`意识，在类unix系统中，不要浪费了`shell`这种神奇的工具，让计算机为我们服务~

![瞅瞅你](https://cdn.colorhub.me/xzDOaNr7Fxor-PyQZV6C1f2rIGocJ4nh--BrR6e-e20/auto/0/500/ce/0/bG9jYWw6Ly8vZjUv/NDkvZjhjZDJiZmVk/MTBiOTFlMjA1ZDli/NTU5NDQwOGQ4ZGRk/MWIzZjU0OS5qcGVn.jpg)



### 基础知识，复习一下

#### 脚本的运行方式

##### 通过文件名执行 ./file_name.sh

注：需要执行权限，可通过 `sudo chmod +x ./file_name.sh` 添加

##### 指定脚本解释器来执行文件 sh file_name.sh

`sh file_name.sh` 就是指定了脚本解释器 `/bin/sh`来解释执行脚本；常见的脚本解释器还有：`/bin/bash`等，我们可以使用`ls -l /bin/*sh`命令来查看当前可用的脚本解释器；

##### 使用. ./file_name或source命令执行脚本

这种方式不会像前两种方式一样fork一个子进程去执行脚本，而是使用当前shell环境执行。我们不必重启shell或者重新登录系统，就能使当前的更改生效。一般用于 .bashrc或者.bash_profile被修改的时候，



#### shebang

定义：我们写一个shell脚本时，总是习惯在最前面加上一行 `#!/binbash`,它就是脚本的`shebang`。

作用：它指示了此脚本运行时的解释器，使用文件名直接执行shell脚本时，必须带上shebang。

使用：可以在shebang后面直接附加选项，执行时我们默认使用选项执行；

如 `test.sh`的`shebang`为 `#!/bin/sh -x`，那我们执行脚本时:

`./test.sh hello`相当于：`bin/sh -x ./test.sh hello`;

注意：在指定脚本解释器来执行脚本时，shebang会被指定的脚本解释器覆盖。





### 自动登录

#### expect解释器

expect是一个能实现自动和交互式任务的解释器，它也能解释常见的shell语法命令，其特色在以下几个命令：

- spawn命令：

`spawn command`命令会fork一个子进程去执行command命令，然后在此子进程中执行后面的命令；

- expect命令：

 它的一般用法为 `expect "string"`,即期望获取到string字符串,可在在string字符串里使用 * 等通配符; `string`与命令行返回的信息匹配后，expect会立刻向下执行脚本；

- set timeout命令：

`set timeout n`命令将expect命令的等待超时时间设置为n秒，在n秒内还没有获取到其期待的命令，expect 为false,脚本会继续向下执行；

- send命令：

一般用法为 `send "string\r"`， 向命令行输入一条信息，`\r` 表示输入回车；

- interact命令：允许用户与当前shell进行交互；



#### 自动登录脚本

创建脚本 `touch aliyun_login_shell.sh`，内容如下：

```bash
  #!/usr/bin/expect
  set user [服务器账号] 
  set host [服务器ip]
  set port [端口号]
  set password [密码]
  set timeout 30
  spawn -p $port $user@$host  #fork一个子进程执行ssh登陆命令；
  expect "password:"
  send "$password\r"
  interact
```

#### 脚本执行登录

执行 `sudo chmod +x ./aliyun_login_shell.sh`命令给shell脚本添加执行权限；

运行 `./aliyun_login_shell.sh`命令，一键登陆成功！

 

优化一下：

>想要要解决的问题：
>
>- 输入`./file_name.sh`命令太长。。。
>- 只能在脚本目录中才能执行，不然使用绝对路径输出的命令更长。

脚本完成了，可是还是有些小瑕疵：

- 输入`./file_name.sh`命令太长。。。
- 只能在脚本目录中才能执行，不然使用绝对路径输出的命令更长。

这里我们想到了linux的alias命令：

- 使用alias命令设置命令别名，例如：  `alias alg=./aliyun_login_shell`, 这样使用`alg`就相当于执行了`./aliyun_login_shell`

- 编辑bash_profile文件，此文件会在终端窗口创建的时候首先执行一次，所以可以帮我们再设置一次别名；

执行命令`vim ~./bash_profile`,在文件内部添加：

```
alias alias_name="/root_dir/../file_name.sh
```

再使用 `. ~./bash_profile`或`source ~./bash_profile`  

从此，我们无论在哪个目录，只要输入`alias_name`命令，回车，真正的一键登陆！



#### iTerm2 工具自动登录
![](https://zhao520a1a.github.io/2020/07/26/shell%E5%AE%9E%E7%8E%B0SSH%E8%87%AA%E5%8A%A8%E7%99%BB%E9%99%86/image-20200726174911885.png)




参考：

https://www.cnblogs.com/qiumingcheng/p/11544569.html



> 喜欢即可关注，关注即可进步。Over!

