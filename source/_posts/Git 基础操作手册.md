

```
title: Git 基础操作手册
tags: [git]
categories: [开发工具]
```

# 仓库操作
## 配置

1、查看配置

```shell
# 列出所有配置
git config --list
# 列出所有配置以及配置文件路径
git config --list --show-origin
# 查看某一项配置
git config <key>
```

2、用户信息

设置全局信息，全局信息只需要设置一次，会在系统上的所有 git 仓库适用。

```shell
git config --global user.name "John Doe"
git config --global user.email johndoe@example.com
```

当你想针对特定项目使用不同的用户名称与邮件地址时，可以在那个项目目录下运行没有 `--global` 选项的命令来配置。

```shell
git config user.name "John Doe"
git config user.email johndoe@example.com
```

3、文本编辑器

git 默认的编辑器是 vim, 可以设置默认编辑器，例如设置为 vscode。

```shell
git config --global core.editor "code --wait --new-window"
```

如果想恢复成 vim，使用下列命令即可。

```shell
git config --global --unset core.editor
```

可以使用编辑器，直接编辑 config 文件。

```shell
# 编辑 global 配置文件
git config --global --edit

# 编辑 local 配置文件
git cofnig --local --edit
```

## 新建或克隆仓库

```shell
# 初始化仓库
$ git init
# 克隆现有仓库
$ git clone https://github.com/libgit2/libgit2 mylibgit
```

# 代码操作

## 增加、删除文件

查看仓库状态。

```shell
$ git status
# 添加文件至暂存区，如果文件是 untracked，被添加后会变成tracked file
$ git add [file1] [file2]

# 添加指定目录到暂存区，包括子目录
$ git add [dir]

# 添加当前目录的所有文件到暂存区
$ git add .

# 添加每个变化前，都会要求确认
# 对于同一个文件的多处变化，可以实现分次提交
$ git add -p

# 删除工作区文件，并且将这次删除放入暂存区
$ git rm [file1] [file2] ...

# 停止追踪指定文件，但该文件会保留在工作区
$ git rm --cached [file]

# 改名文件，并且将这个改名放入暂存区
$ git mv [file-original] [file-renamed]
```

## 提交代码

```shell
# 提交暂存区到仓库区
$ git commit -m [message]

# 提交暂存区的指定文件到仓库区
$ git commit [file1] [file2] ... -m [message]

# 提交工作区自上次commit之后的变化，直接到仓库区
$ git commit -a

# 使用一次新的commit，替代上一次提交
# 如果代码没有任何新变化，则用来改写上一次commit的提交信息
$ git commit --amend -m [message]

# 重做上一次commit，并包括指定文件的新变化
$ git commit --amend [file1] [file2] ...
```

## 撤销

很多时候使用 `git status` 命令会提示某些操作。

例如：

```shell
$ git status
On branch master
Changes to be committed:
  (use "git reset HEAD <file>..." to unstage)

    renamed:    README.md -> README
    modified:   CONTRIBUTING.md
```

注意上述括号中的提示 **(use "git reset HEAD …" to unstage)**。

```shell
# 丢弃工作区的文件更改
$ git restore <file>

# 将文件从暂存区移动到工作区，但是文件依旧保留更改
$ git restore --staged <file>
```

reset 和 revert 的区别：reset 指回退到某个 commit，而 revert 是添加一个新的 commit 用来回退到某个 commit。

reset 基本用法：

```shell
# 回退时会保留源码，修改的源码保存在暂存区
$ git reset --soft <commit>

# reset 的默认行为，回退时会保留源码，修改的源码保存在工作区
$ git reset --mixed <commit>

# 会退时不会保留源码，危险操作！！
$ git reset --hard <commit>
```

reset 后想要推送到远程仓库，这是个比较危险的操作，因为会清除提交历史，需要加上 `--force`:

```shell
$ git push --force
```

`git revert` 只不过是用一个新的提交去回滚代码，所以与普通的提交没有本质区别，不会影响其他的。

## 查看信息

```shell
# 显示版本历史
$ git log

# 显示版本历史，以及每次commit发生的变更的文件
$ git log --stat

# 显示最近的2次提交的文件的差异
$ git log -p -2

# 每个提交信息显示为一行
$ git log --pretty=oneline

# 显示最近两周的所有提交
$ git log --since=2.weeks

# 搜索提交历史，根据关键词
$ git log -S [keyword]

# 显示暂存区和工作区的差异
$ git diff

# 显示暂存区和上一个commit的差异
$ git diff --cached [file]

# 显示工作区与当前分支最新commit之间的差异
$ git diff HEAD

# 显示两次提交之间的差异
$ git diff [first-branch]...[second-branch]
```

# 分支操作

## 远程协作

```shell
# 查看远程服务器的简写
$ git remote

# 显示需要读写远程仓库使用的 Git 保存的简写与其对应的 URL
$ git remote -v

# 显示摸个远程仓库的详细信息
$ git remote show [remote]

# 添加一个新的远程 Git 仓库，同时指定一个方便使用的简写
$ git remote add <shortname> <url>

# 从远程仓库中拉取代码，但不会合并
$ git fetch [remote]

# 取回远程仓库的变化，并与本地分支合并
$ git pull [remote] [branch]

# 将 <branch> 分支上的代码推送到 <remote>
$ git push <remote> <branch>

# 推送所有分支到远程仓库
$ git push [remote] -all

# 修改远程仓库的简写名
$ git remote rename <old> <new>

# 移除远程仓库
$ git remote remove <remote>

# 删除远程分支
$ git push origin --delete <branch>
```

## 标签

像其他版本控制系统（VCS）一样，Git 可以给仓库历史中的某一个提交打上标签，以示重要。

1、显示标签

```shell
# 按字母顺序列出已有的标签
$ git tag

# 显示标签详细信息
$ git show [tag]
```

2、创建标签

Git 支持两种标签：轻量标签（lightweight）与附注标签（annotated）。附注标签是存储在 Git 数据库中的一个完整对象， 它们是可以被校验的，其中包含打标签者的名字、电子邮件地址、日期时间， 此外还有一个标签信息，并且可以使用 GNU Privacy Guard （GPG）签名并验证。 通常会建议创建附注标签，这样你可以拥有以上所有信息。但是如果你只是想用一个临时的标签， 或者因为某些原因不想要保存这些信息，那么也可以用轻量标签。

用 `-a` 选项指定创建附注标签，`-m` 表示标签信息，如果没有为附注标签指定一条信息，Git 会启动编辑器要求你输入信息。

```shell
# 在当前 commit 创建 v1.4 标签，并指定信息：my version 1.4
$ git tag -a v1.4 -m "my version 1.4"
```

创建轻量标签，不需要使用 `-a`、`-s` 或者 `-m` 选项，只需要提供标签名字：

```shell
# 在当前 commit 创建 v1.4 的轻量标签
$ git tag v1.4
```

也可以对过去的提交打标签，需要指定提交的 hash。

```shell
# 附注标签
$ git tag -a v1.4 9fceb02

# 轻量标签
$ git tag v1.4 9fceb02
```

3、共享标签

默认情况下，`git push` 命令并不会传送标签到远程仓库服务器上。 在创建完标签后你必须显式地推送标签到共享服务器上。

```shell
# 类似推送分支一样，推送 tag
$ git push origin <tagname>
```

使用 `--tags` 选项，可以一次性推送很多标签。

```shell
$ git push <remote> --tags
```

4、删除标签

```shell
# 删除本地仓库上的标签
$ git tag -d <tagname>
```

上述命令不会从远程仓库上移除这个标签，必须使用 `git push <remote> :refs/tags/<tagname>` 来更新远程仓库。

第二种更直观的删除远程标签的方式是：

```shell
$ git push origin --delete <tagname>
```

5、查看某个标签的文件版本

```shell
# 查看指定 tag 的文件
$ git chekcout <tagname>
```

使用 `git checkout` 命令， 会使你的仓库处于“分离头指针（detached HEAD）”的状态，如果你当前做出了修改，新的提交将不属于任何分支，并且将无法访问，除非通过确切的提交哈希才能访问。因此，如果你需要进行更改，比如你要修复旧版本中的错误，那么通常需要创建一个新分支：

```shell
$ git checkout -b version2 v2.0.0
Switched to a new branch 'version2'
```

然后，你可以在 `version2` 分支上做出修改。

## 分支

```shell
# 查看本地分支列表
$ git branch

# -v 标记查看本地分支的最后一次提交
$ git branch -v

# --merged 标记可以查看已合并到当前分支的分支列表
$ git branch --merged

# --no-merged 标记可以查看未合并到当前分支的分支列表
$ git branch --no-merged

# 新建分支
$ git branch <branch>

# 切换分支
$ git checkout <branch>

# 新建分支后，并切换到新建的分支
$ git checkout -b <branch>

# 合并分支到当前分支
$ git merge <branch>

# 删除分支
$ git branch -d <branch>
```

# 子模块操作
## submodule

```shell
# 添加 submodule
$ git submodule add <submodule_url>

# 初始化配置、更新子模块
$ git submodule init && git submodule update

# 初始化配置、更新子模块（包括嵌套的子模块）
$ git submodule init && git submodule update --init --recursive

# 克隆主仓库时，初始化并更新子模块（包括嵌套的子模块）
$ git clone <main_repo> --recurse-submodules

# 初始化并获取子模块的代码（不包括嵌套子模块），与 'git submodule init && git submodule update' 等价
$ git submodule update --init

# 初始化并获取任何嵌套的子模块
$ git submodule update --init --recursive

# 切换子模块跟踪的分支
$ git config -f .gitmodules submodule.<submodule_name>.branch <branch_name>

# 抓取子模块的更新
$ git submodule update --remote [submodule_name]

# 拉取代码，包括子模块以及嵌套子模块
$ git pull --recurse-submodules
```

默认情况下，在诸项目中使用 `git pull` 命令会递归的抓取子模块的更改，但是它不会更新子模块。你需要运行 `git submodule update --init --recursive` 来完成子模块的更新。如果你想要一步达到这个效果，可以使用 `git pull --recurse-submodules`

另一个需要注意的是，当运行 `git submodule update` 从子模块仓库中抓取修改时，Git 将会获得这些改动并更新子目录中的文件，但是会将子仓库留在一个称作 [“游离的 HEAD 状态”](https://stackoverflow.com/a/58142219)，这意味着没有本地工作分支（例如 ”master“）跟踪改动。如果没有工作分支跟踪改动，也就意味着即便你将更改提交到了子模块，这些更改可能会在下次运行 `git submodule update` 时丢失，所以在子模块中跟踪这些修改，还需要一些额外的步骤。首先，进入每个子模块并检出其相应的工作分支，接着如果你做了更改就需要告诉 Git 它该做什么，然后云心 `git submodule update --remote` 从上游拉取新工作，你可以选择将他们合并到你的本地工作中，也可以尝试将你的工作变基到新的更改上。

 

## 参考

[Git 基础操作](https://pengfeixc.com/blogs/developer-handbook/git-commands)