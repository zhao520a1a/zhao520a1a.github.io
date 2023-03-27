---
title: Redis之源码结构属性
tags: [redis]   
categories: [源码解读]
---

[TOC]

#### redisServer
``` c
struct redisServer {
int dbnum;//服务器的数据库数量，值由服务器配置的“databases”选项决定，默认为16
redisDb *db;//数组，保存着服务器中的所有数据库
 
list *clients;//一个链表，保存了所有客户端状态，每个链表元素都是“redisClient”结构
 
/*服务器时间缓存*/ 
time_t unixtime;//保存秒级精度的系统当前UNIX时间戳，减少获取系统当前时间的系统调用次数，100毫秒更新一次
long long mstime;//保存毫秒级精度的系统当前UNIX时间戳
unsigned lruclock;//默认每10秒更新一次，用于计算数据库键的空转时长，数据库键的空转时长 = 服务器的“lruclock”属性值 - 数据库键值对象的“lru”属性值
 
/*RDB持久化*/
long long dirty;//修改计数器（记录距离上一次成功执行 save 命令或者 bgsave 命令之后，Redis服务器进行了多少次修改）
time_t lastsave;//它是一个时间戳，记录上一次成功执行 save 命令或者 bgsave 命令的时间
/*AOF持久化*/
sds aof_buf;//AOF缓冲区
 
int cronloops;//serverCron函数的运行次数计数器
```

#### redisDb
``` c
struct redisDb {
dict *dict;//数据库键空间字典，保存数据库中所有的键值对
dict *expires;//过期字典，保存数据库中所有键的过期时间
dict *watched_keys;//字典，正在被WATCH命令监视的键
};
```



#### redisClient
``` C
typedef struct redisClient {
    // 当前正在使用的数据库
    redisDb *db;
    // 当前正在使用的数据库的 id （号码）
    int dictid;
    
    // 套接字描述符
    int fd;
    // 客户端的名字
    robj *name;             
    // 输入缓冲区
    sds querybuf;
  
    // 命令与命令参数数组
    robj **argv;
    // 记录argv数组的长度
    int argc;
    // 记录被客户端执行的命令
    struct redisCommand *cmd, *lastcmd;
     
    // 记录buf数组已使用的字节数量
    int bufpos;
    // 输出缓冲区
    char buf[REDIS_REPLY_CHUNK_BYTES];
    
    // 客户端状态标志
    int flags;              
    // 代表认证的状态： 0 代表未认证， 1 代表已认证
    int authenticated;      /* when requirepass is non-NULL */
    
    // 创建客户端的时间
    time_t ctime;           
    // 客户端最后一次和服务器互动的时间
    time_t lastinteraction; 
    // 客户端的输出缓冲区超过软性限制的时间
    time_t obuf_soft_limit_reached_time;
   
    /*主从复制*/
    // 复制状态
    int replstate;          
    // 用于保存主服务器传来的 RDB 文件的文件描述符
    int repldbfd;           /* replication DB file descriptor */
    // 读取主服务器传来的 RDB 文件的偏移量
    off_t repldboff;        
    // 主服务器传来的 RDB 文件的大小
    off_t repldbsize;         
   
    // 事务状态
    multiState mstate;             
    // 被监视的键
    list *watched_keys;      
} redisClient;

```
