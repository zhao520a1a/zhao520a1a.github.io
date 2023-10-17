---
title: Java HashMap 内部原理
tags: [java]
categories: [内部原理]
date: 2019-08-01
cover: https://1.bp.blogspot.com/-7qlGiyxNuGc/Xd0UQjr3jBI/AAAAAAAAGj8/VqXHcWZ_WYUv13QLBzbIOBRv2bXL3Wn6ACPcBGAYYCw/s1600/How%2BHashMap%2BWorks%2BInternally%2Bin%2BJava.png
---

## 概述

> 脑图：https://www.processon.com/diagraming/5bd57d49e4b021eeb31f7e06

### 版本不同

首先jdk1.7和jdk1.8内部实现有不同；
先给结论，镇楼：
| 对比 | 内部结构 | 计算新下标 | 扩容机制  
| --- | --- | --- | --- |
| jdk1.7 | 数组 + 链表 | 通过`hash&newCap-1`计算出新下标，依次进行数据迁移| 先进行扩容再插入，执行的是头插法；会出现逆序和环形链表死循环问题； |
| jdk1.8 | 数据 + 链表 + 红黑树 | 通过`hash&oldCap`遍历元素检查高一位big值（0-下标不变，1-下标改变），组装成新的链表，统一进行数据迁移 | 先进行插入再进行扩容，执行的是尾插法，直接插到链表尾部/红黑数树，不会出现逆序和环形链表死循环问题 |

注：扩容操作时，一个元素的新坐标，结果只有两种： 要么在原来的位置，要么在 （原来的位置+原数组大小）的位置。

### 为什么要改动?

遇到的问题：由于JDK中采用`链地址法`解决 哈希冲突，当冲突越来越多，导致链表越来越长，导致性能下降 。同时jdk1.7采用插法，存在死锁问题。

解法：当链表达到一定的阈值（默认为8）并且数组长度要小于64,会进行扩容操作，将一个长链表拆成两个短链表。当链表达到一定的阈值（默认为8）并且数组长度要大于等于64，那就采用红黑树存储；来把时间复杂度从O（n）变成O（logN）提高了效率；

## 详述

### jdk1.7 头插法问题

并发情况下，如果插入元素的两个线程都调用了rehash方法(扩容方法)，会产生环形链表，造成死锁。

1. 线程A先执行，执行完Entry<K,V> next = e.next;这行代码后挂起;
2. 然后线程B完整的执行完整个扩容流程
3. 接着线程A唤醒，继续之前的往下执行，当while循环执行3次后会形成环形链表。
   注:hashmap成环原因的代码出现在transfer代码中，也就是扩容之后的数据迁移部分;
   具体细节，推荐：https://blog.csdn.net/thqtzq/article/details/90485663

### jdk1.8 HashMap内部结构

不为人知的小细节：

- TreeNode同时也是一个双向链表节点； 规定：这个双向链表的头节点，必须是红黑树的根节点。

- 当链表达到一定转红黑树的阈值，但数组长度要小于64，是不会转成红黑树的，这时会进行resize()操作，将一个长链表拆成两个短链表。

- 当前满足转红黑树的条件；假设链表转红黑树的阈值是8，程序是在将第9个元素插入链表后，再将链表转成红黑树的。

- 红黑树插入节点时，节点间的比较规则：

  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/9E8D40D7-EAD8-4A07-9F68-8EA32319A369-3094492.png" alt="img" style="zoom:80%;" />

### 源码解读

- HashMap基本属性

  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/D5C5B782-15C6-44B0-BD41-14648DEAED6F.png" alt="img" style="zoom:67%;" />

- 元素寻址流程

  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/BC1205EC-D6B3-465F-96D2-6AFBC08E734C.png" alt="img" style="zoom:67%;" />

  获得hash值：
  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/7FCE1BFB-8FA8-4183-8EBE-176CB0B0F44F-3094608.png" alt="img" style="zoom:75%;" />
  获得下标值:
  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/E7B32DCC-DA92-4D23-B2D9-9C9E066630E1-3094658.png" alt="img" style="zoom:75%;" />
  带你看看位运算：
  `hash = hashCode ^ hashCode>>>16`
  `index = hash & (cap-1)`
  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/707BDA78-49AC-4113-8918-D90AB83AEE4C-3094671.png" alt="img" style="zoom:75%;" />

- jdk1.8扩容时，是如何标记出当前数据是否需要迁移到新的坐标下？
  检查高一位的bit值，确定是否移动位置： 0 or 1
  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/E3C31D58-AAD3-45AE-88E5-6A818A491827-3094691.png" alt="img" style="zoom:75%;" />
  迁移规则：
  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/36639C5C-DC03-415C-9438-FCCF1F8D3A40-3094709.png" alt="img" style="zoom:75%;" />

- 向红黑树中插入节点时，是如何进行比较的？
  <img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/F3382595-C4A1-4166-B58A-69737A31E7DF-3094722.png" alt="img" style="zoom: 50%;" />

- 链表是如何转移成红黑树的？
  先将单向链表转移成双向链表，双向链表树化成红黑树结构；

- 扩容是红黑树如何复制转移？

1. 以双向链表形式遍历红黑树节点，标记出那些节点需要被转移；
2. 统计出需要转移和不需要的数量；
3. 同树->链表的阈值做对比，按比较结果，决定扩容后是树结构还是链表结构。

### 更新元素

下面我带着大家， 当我们向HashMap中添加和删除元素时，看它内部偷偷的被这我们都干了啥玩意？
添加元素操作： public V put(K key, V value)
<img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/put%E6%96%B9%E6%B3%95%E6%B5%81%E7%A8%8B%E5%9B%BE-3094767.png" alt="img" style="zoom:80%;" />

#### 总结

<img src="Java%20HashMap%20%E5%86%85%E9%83%A8%E5%8E%9F%E7%90%86/3A706DA9-ED7E-46D5-AE53-1C0D7B6FB379-3094780.png" alt="img" style="zoom:75%;" />
