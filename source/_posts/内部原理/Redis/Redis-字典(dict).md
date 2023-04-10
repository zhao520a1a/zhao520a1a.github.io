---
title: Redis-字典(dict)
tags: [redis]   
categories: [内部原理]
date: 2020-05-01
description: Redis 的底层存储结构？
cover: https://github.com/zhao520a1a/zhao520a1a.github.io/blob/hexo/source/cover/Redis-dict.jpg?raw=true
---



> 字典，又称为符号表、关联数组、映射，是一种用于保存键值对的抽象数据结构。
> Redis使用C语言并没有内置中这种数据结构，所以Redis构建了自己的字典实现。

#### 用途
1. 是哈希键的底层实现之一；当一个哈希键包含了数量比较多的元素，或者包含的元素都是比较长的字符串时，就会选用字典作为哈希键的底层实现。
2. Redis的数据库就是使用字典作为底层实现的，对数据的CURD操作也是对构建在对字典的操作上的。

##### 字典的结构
- 整体结构图
<img src="Redis-字典(dict)/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3N1bnNoaW5lX1lH,size_16,color_FFFFFF,t_70" alt="img" />

- dict结构，在Redis中的字典dict.h/dict中定义：
``` c
typedef struct dict{
    //类型特定函数(dictType保存了一簇用于操作特定类型键值对的函数，Redis会为用途不同的字典设置不同的类型特定函数)
    dictType *type;
    //私有数据（保存了需要传给dictType类型特定函数的可选参数）
    void *privdata;
    //哈希表(数组中每一项都是一个dictht哈希表，一般情况下，字典只是用ht[0]哈希表，ht[1]只会在对hr[0]进行rehash时使用)
    dictht ht[2];
    //rehash索引（记录rehash目前进度）
    //未在进行rehash时，值为-1(rehashing not in progress if rehashidx == -1)
    int rehashidx;
}dict;
```

dictType结构:
``` c
typedef struct dictType{
    //计算哈希值的函数
    unsigned int (*hashFunction)(const void *key);
    //复制键的函数
    void *(*keyDup)(void *privdata,const void *key);
    //复制值的函数
    void *(*valDup)(void *privdata,const void *obj);
    //对比键的函数
    int (*keyCompare)(void *privdata,const void *key1,const void *key2);
    //销毁键的函数
    void (*keyDestructor)(void privdata,void *key);
    //销毁值的函数
    void (*valDestructor)(void *privdata,void *obj);
}dictType;
```


- dictht结构，Redis字典所使用的哈希表有dict.h/dictht定义：
``` c
typedef struct dictht{
    //哈希表数组
    dictEntry **table;
    //哈希表大小(即table数组大小)
    unsigned long size;
    //哈希表大小掩码，用于计算索引值
    //总是等于size-1
    //这个属性和哈希值一起决定一个键应该被放到table数组的哪个索引上面。
    unsigned long sizemask;
    //该哈希表已有节点的数量
    unsigned long used;
}dictht;
```

- dictEntry结构，哈希表节点使用dictEntry结构表示。 table属性是一个数组，数组中的每个元素都是一个指向dict.h/dictEntry结构的指针。
``` c
typedef struct dictEntry{
    //键
    void *key;
    //值
    union{
        void *val;
        uint64_tu64;
        int64_ts64;
    }v;
    //指向下个哈希表节点，形成链表
    struct dictEntry *next;
}dictEntry;
```


#### 字典的实现
##### 计算哈希值和索引值
``` c
//使用字典设置的哈希函数，计算键key的哈希值
hash = dict -> type -> hashFunction(key);
//使用哈希表的sizemask属性和哈希值，计算出索引值
//根据情况不同，ht[x]可以是ht[0]或者ht[1]
index = hash & dict -> ht[x].sizemask;
```
注：此处hash值算法为MurmurHash2。MurmurHash算法要比MD5算法要快，且有很好的随机分布性.

##### 解决键冲突
> 键冲突：有两个或以上数量的键被分配到了哈希表数组的同一个索引上面。
> Redis使用链地址法解决键冲突。

<img src="Redis-字典(dict)/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3N1bnNoaW5lX1lH,size_16,color_FFFFFF,t_70_2" alt="img" />
注：因为dictEntry结点组成的链表没有指向链表表尾的指针（即图4-6的k1节点），所以为了速度考虑，程序总是将新节点添加到链表的表头位置（复杂度为O(1)），排在其他已有节点的前面。

##### rehash
> 1. 当哈希表保存的键值对数量太多或者太少时，程序需要对哈希表的大小进行相应的扩展或者收缩。
> 2. rahash：指的是重新计算键的哈希值和索引值，然后将键值对放置到ht[1]哈希表的指定位置上。

`负载因子 = 哈希表已保存节点数量 / 哈希表大小`
``` 
load_factor = ht[0].used / ht[0].size;
```

###### 扩展触发条件
（1）服务器目前没有在执行BGSAVE命令或者BGREWRITEAOF命令，并且哈希表的负载因子大于等于1。
（2）服务器目前正在执行BGSAVE命令或者BGREWRITEAOF命令，并且哈希表的负载因子大于等于5。
###### 收缩触发条件
哈希表负载因子小于0.1；

###### 扩展或收缩步骤
1. 为字典的ht[1]哈希表分配空间，分配空间的大小取决于
①要执行的操作--扩展或收缩
②ht[0]当前包含的键值对数量（即ht[0].used的值），
扩展:大小为第一个大于等于 ht[0].used*2 的 2^n。
收缩:大小为第一个大于等于 ht[0].used 的 2^n。
2. 将保存在ht[0]中的所有键值对rehash到ht[1]上。
3. 当ht[0]包含的所有键值对都迁移到了ht[1]之后（ht[0]变为空表）,释放ht[0]，将ht[1]设置为ht[0]，并创建一个新的ht[1]空的哈希表，为下次rehash做准备。


###### 渐进式rehash详细步骤

1. 为ht[1]分配空间。
2. 在字典中维持一个索引计数器变量rehashidx，并将它的值设置为0，0表示rehash工作正式开始。
3. 在rehash期间，每次对字典执行添加、删除、查找或者更新操作时，程序除了执行指定的操作以外，还会顺带将ht[0]哈希表在rehashidx索引上的所有键值对rehash到ht[1]，当rehash工作完成之后，程序将rehashidx属性的值增一。
4. 随着自点操作的不断执行，最终在某个时间点上，ht[0]的所有兼职对都会被rehash至ht[1]，这时程序将rehashidx属性的值设为-1,-1表示rehash操作已完成。
注：在进行渐进式rehash的过程中，字典会同时使用ht[0]和ht[1]两个哈希表，所以<u>在渐进式rehash进行期间，字典的删除（delete）、查找（find）、更新（update）等操作会在两个哈希表上进行。</u>例：要在字典里面查找一个键的话，程序会先在ht[0]里面进行查找，如果没找到的话，就会继续到ht[1]里面进行查找。
另外，添加操作则只在ht[1]中执行，这一措施保证了ht[0]包含的键值对数量会只减不增，并随着rehash操作的执行而最终变成空表。
注意:观察在整个rehash过程中，字典的rehashidx属性是如何变化的。
<img src="Redis-字典(dict)/watermark,type_ZmFuZ3poZW5naGVpdGk,shadow_10,text_aHR0cHM6Ly9ibG9nLmNzZG4ubmV0L3N1bnNoaW5lX1lH,size_16,color_FFFFFF,t_70_1" alt="img" />
&nbsp;

###### 思考题
`为什么触发扩展条件的负载因子不同？`
原因： 在执行BGSAVE或BGREWRITEAOF命令时，Redis需要创建当前服务器进程的子进程，而大多数操作系统都采用写时复制（copy-on-write）技术来优化子进程的使用效率，所以在子进程存在期间，服务器会提高执行扩展操作所需的负载因子，从而尽可能地避免在子进程存在期间进行哈希表扩展操作，这可以避免不必要的内存写入操作，最大限度的节约内存。
`为什么rehash是分多次、渐进式地完成的` 
原因：哈希表里保存的键值对数量非常庞大时（像四百万、四千万、四亿个键值对），一次性、集中式地完成庞大的计算量可能会导致服务器在一段时间内停止服务。`采用分而治之的方式，将rehash键值对所需的计算工作均摊到对字典的每个添加、删除、查找和更新操作上，从而避免了集中式rehash而带来的庞大计算量。`
#### 小结
1. 字典被广泛用于实现Redis的各种功能，其中包括数据库和哈希键。
2. Redis中的字典使用哈希表作为底层实现，每个字典带有两个哈希表，一个平时使用，另一个仅在rehash时使用。
3. 当字典被用作数据库的底层实现，或者哈希键的底层实现时，Redis使用MurmurHash2算法来计算键的哈希值。
4. 哈希表使用`链地址法来解决键冲突`，被分配到同一个索引上的多个键值对会连接成一个单向链表。
5. 在对哈希表进行扩展或者收缩操作时，程序需要将现有哈希表包含的所有键值对rehash到新哈希表里面，并且这个rehash过程并不是一次性地完成的，而是渐进式地完成的。
