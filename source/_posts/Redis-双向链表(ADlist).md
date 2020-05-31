---
tags: [redis内部结构]   
categories: redis
---

[TOC]

>  Redis使用C语言并没有内置中这种数据结构，所以Redis构建了自己的链表实现。

#### 用途
1. 在3.2之前是列表键的底层实现之一，在3.2之后被quicklist替代。
2. 发布与订阅、慢查询、监视器等功能
3. Redis服务器使用链表保存多个客服端的状态信息
4. 构建客户端输出缓冲区(outpub buffer)

#### 数据结构
![c7f6fa8e6cd30bc4a29bce6b63a8834e](Redis-双向链表(ADlist).resources/14A882FC-34BD-47D0-A891-1A85CFBEC5E1.png)
每个链表使用一个list结构来表示；
表头的前置节点和表尾的后置节点都可以指向NULL,因此Redis实现的是`无环链表`。
 ![a579f0ea94ddb9b7cd256ab6e35c4fbc](Redis-双向链表(ADlist).resources/ABE04246-074F-47A9-A8E8-5DECE3BF1045.png)
 
 ![aa9d6dc667dd5b6976b551ab05ea8ea8](Redis-双向链表(ADlist).resources/A92F8473-2BD2-4C86-88AD-5B88FD68D2C5.png)
 
 
 
