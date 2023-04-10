---
title: Redis-双向链表(ADlist)
tags: [redis]   
categories: [内部原理]
date: 2020-05-01
description: Redis 的底层存储结构？
cover: https://github.com/zhao520a1a/zhao520a1a.github.io/blob/hexo/source/cover/Redis-adlist.jpg?raw=true
---




>  Redis使用C语言并没有内置中这种数据结构，所以Redis构建了自己的链表实现。

#### 用途
1. 在3.2之前是列表键的底层实现之一，在3.2之后被quicklist替代。
2. 发布与订阅、慢查询、监视器等功能
3. Redis服务器使用链表保存多个客服端的状态信息
4. 构建客户端输出缓冲区(outpub buffer)

#### 数据结构
<img src="Redis-双向链表(ADlist)/14A882FC-34BD-47D0-A891-1A85CFBEC5E1.png" alt="img" />
每个链表使用一个list结构来表示；
表头的前置节点和表尾的后置节点都可以指向NULL,因此Redis实现的是`无环链表`。
 <img src="Redis-双向链表(ADlist)/ABE04246-074F-47A9-A8E8-5DECE3BF1045.png" alt="img" />

 <img src="Redis-双向链表(ADlist)/A92F8473-2BD2-4C86-88AD-5B88FD68D2C5.png" alt="img" />

 

