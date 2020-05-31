---
tags: [redis内部结构]   
categories: redis
---

[TOC]

> 前言： quicklist是一个3.2版本之后新增的基础数据结构，是redis自定义的一种复杂数据结构，`将ziplist和adlist结合到了一个数据结构中`。主要是作为
list的基础数据结构。
在3.2之前，list是根据元素数量的多少采用ziplist或者adlist作为基础数据结构，`3.2之后统一改用quicklist`.
 

#### 定义
从数据结构的角度来说quicklist结合了两种数据结构的优缺点，复杂但是实用。通过将每个压缩表用双向链表的方式连接起来，来寻求一种收益最大化。

#### 特点
quicklist目的是最大程度减小内存空间占用并保证性能
- 链表(adlist)在插入、删除节点的时间复杂度很低,但是`内存利用率低`，且由于内存不连续容易产生内存碎片。利用ziplist减少node数量。
- 压缩表(ziplist)内存连续，存储效率高；但是`插入和删除的成本太高`，需要频繁的进行数据搬移、释放或申请内存。为避免长度较长的ziplist修改时带来的内存拷贝开销，通过配置项配置合理的ziplist长度。

#### 核心数据结构
##### quicklist
quicklistNode实际上就是对ziplist的进一步封装，quicklist包含多个quicklistNode，quicklistNode由ziplist来保存数据。
![17755a553f9431d5c834be7591b3d94c](Redis-快速列表(quicklist).resources/4D55BD28-D972-4447-A955-A82BBB38E9FA.png)
注：图示中两端的节点，是没有被压缩的。它们的数据指针zl指向真正的ziplist。中间的其它节点是被压缩过的，它们的数据指针zl指向被压缩后的ziplist结构，即一个quicklistLZF结构。

``` c
typedef struct quicklist {
    quicklistNode *head;    // 头结点
    quicklistNode *tail;    // 尾节点
    unsigned long count;    // 所有数据的数量
    unsigned int len;       // quicklist节点数量
    int fill : 16;          // 单个节点的负载比例，即：单个ziplist的大小限制 
    unsigned int compress : 16;   // 压缩深度
} quicklist;
```
> 注：由于quicklist结构包含了压缩表和链表，那么`每个quicklistNode的大小就是一个需要仔细考量的点`。
如果单个quicklistNode存储的数据太多，就会影响插入效率；
如果单个quicklistNode太小，就会变得跟链表一样造成空间浪费。
- quicklist通过属性fill对单个quicklistNode的大小进行限制：fill可以被赋值为正整数或负整数，
- `当fill值为负数时`，表示单个节点最大的允许的`存储空间`：
-1：单个节点最多存储4kb (推荐)
-2：单个节点最多存储8kb (推荐,默认值)
-3：单个节点最多存储16kb (不推荐)
-4：单个节点最多存储32kb (非常不推荐)
-5：单个节点最多存储64kb (通常情况下不要设置这个值)
- `当fill值为正数时`，表示单个节点最大允许的`元素个数`，最大为32768个
注：<u>通常在-2或-1时, 性能表现最好在redis内部使用中，默认的最大单节点数据量设置是-2，也就是8kb</u>;

##### quicklistNode
``` c
typedef struct quicklistNode {
    struct quicklistNode *prev; // 前一个节点
    struct quicklistNode *next; // 后一个节点
    unsigned char *zl;  // ziplist指针
    unsigned int sz;  // ziplist的内存大小,,单位是字节
    unsigned int count : 16;  // zpilist中数据项的个数,它是一个 16 bit 大小的字段, 所以一个 quicklistNode 最多也只能存储 65536 个元素
    unsigned int encoding : 2;  // 当前节点中的 ziplist 的编码方式,1 1(RAW) 表示默认的方式存储, 2(LZF) 表示用 LZF 算法压缩后进行的存储
    unsigned int container : 2;  // 表示 quicklistNode 当前使用哪种数据结构进行存储的, 目前支持的也是默认的值为 2(ZIPLIST), 未来也许会引入更多其他的结构
    unsigned int recompress : 1;  // 压缩标志,1表示压缩
    unsigned int attempted_compress : 1; //  节点是否能够被压缩,只用在测试
    unsigned int extra : 10; //是剩下多出来的 bit, 可以留作未来使用
} quicklistNode;
```
注：这里从变量count开始，都采用了位域的方式进行数据的内存声明，使得6个unsigned int变量只用到了一个unsigned int的内存大小。





#### 插入节点过程
如果你插入一个新的元素到 quicklist 中
- 如果当前的 quicklist 是空的, 创建一个新的 ziplist 并且把这个元素插入到 ziplist 中;
- 如果当前的 quicklist 不是空的, 如果这个要插入的节点还有位置(count < fill), 找到你想要插入的位置,插入到当前节点的 ziplist 中;
- 如果没位置了, 但是你插入的是 quicklist 的头部或者尾部(lpush/rpush), 创建一个新的 ziplist 并进行插入
- 不然的话(没位置并且插入中间), 把中间的 ziplist 按照你插入的位置为界, 分成两个 ziplist, 插入并连接起来
 
#### 删除节点过程
在 redis/src/quicklist.c 中定义了如下函数原型 int quicklistDelRange(quicklist *quicklist, const long start, const long count), 这个函数会遍历所有的节点, 知道你指定的范围都删除为止。
 
#### 示例1
- 我在配置文件做了如下两行的更改
```
list-max-ziplist-size 3
list-compress-depth 0
```
- 插入首个节点
```
127.0.0.1:6379> lpush lst 123 456
(integer) 2
127.0.0.1:6379> object encoding lst
"quicklist"
```
 ![7e4dfc9484485e3614c7e3df722a6d6e](Redis-快速列表(quicklist).resources/E509CE4D-92D6-4D5A-9430-0535ED2F989E.png)
- 再插入一个节点
 ```
 127.0.0.1:6379> lpush lst 789
(integer) 4
 ```
注： 因为第一个节点中的元素数量已经大于等于 fill 中的值了, 一个新的节点会被创建。fill 仍然为 3, len 变为 2, count 变为 4
![7113fc22174b94426a900d545d307170](Redis-快速列表(quicklist).resources/A00CD00B-9D55-425D-8791-EBA17AF7A227.png)

#### 示例2
- 我在配置文件做了如下两行的更改
```
list-max-ziplist-size 3
list-compress-depth 0
```
- 插入节点
```
127.0.0.1:6379> del lst
(integer) 1
127.0.0.1:6379> lpush lst aa1 aa2 aa3 bb1 bb2 bb3 cc1 cc2 cc3
(integer) 8
```
![f0945c027bade24a3ad38d783389cc58](Redis-快速列表(quicklist).resources/23D940D1-1262-441C-B58B-BD72DF12BD86.png)
- 将节点插入到中间部分
```
127.0.0.1:6379> linsert lst after bb2 123
(integer) 10
结果：cc3 cc2 cc1 bb3 bb2 123 bb1  aa3 aa2 aa1 
```
注：因为存储了值 bb2 的 quicklistNode 是满的了, 这个节点会被拆开  
![aac22087ede59ca425088cd0192941a2](Redis-快速列表(quicklist).resources/9E311D76-E91B-4600-8058-DDD12356FB67.png)

#### Redis配置
##### list-max-ziplist-size
Redis的配置文件中，给出了每个ziplist中长度的设定，可通过配置项配置合理的ziplist长度，设置根据场景而定。对应quicklist的fill属性，取值含义同fill属性值。例如
``` 
list-max-ziplist-size -2 
```
##### list-compress-depth
因为链表的特性，一般首尾两端操作较频繁，中部操作相对较少，所以redis提供`压缩深度配置`：
参数list-compress-depth的取值含义如下：
0: 是个特殊值，表示都不压缩。这是Redis的默认值。
1: 表示quicklist两端各有1个节点不压缩，中间的节点压缩。
2: 表示quicklist两端各有2个节点不压缩，中间的节点压缩。
3: 表示quicklist两端各有3个节点不压缩，中间的节点压缩。
依此类推，最大16bit


#### 小结
- 快速列表将压缩表和链表结合到了一个数据结构中`。主要是作为list的基础数据结构；
- 可通过配置项`list-max-ziplist-size`设定合理的ziplist大小；值为负代表从字节大小限定，值为正代表元素个数限定；
- 可通过配置项`list-compress-depth`设定压缩深度配置；

> 参考：
https://github.com/zpoint/Redis-Internals/blob/5.0/Object/list/list.md
http://czrzchao.com/redisSourceQuicklist#quicklist
https://blog.csdn.net/qq_31720329/article/details/99938219
