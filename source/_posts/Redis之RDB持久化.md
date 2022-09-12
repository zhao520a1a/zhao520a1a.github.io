---
tags: [redis]   
categories: [源码解读]
---

[TOC]

#### 定义
-  RDB 是 Redis 将 server 端的内存中的键值对以二进制的方式，持久化存储的一种文件形式。 文件中，一般会以 `对象的长度+对象`的格式来存储，只要根据这个格式，就能渐进的遍历整个文件。 
- Redis 还支持开启 LZF 的压缩算法，可以牺牲 CPU 时间，来减少 RDB 文件的大小；如果开启LZF并且超过20个 bytes 时， 会将压缩后的字符写入文件。

#### 触发方式
##### 自动触发
Redis通过配置save参数，来触发RDB持久化条件。
　　默认如下配置：
```
save 900 1：表示900 秒内如果至少有 1 个 key 的值变化，则保存
save 300 10：表示300 秒内如果至少有 10 个 key 的值变化，则保存
save 60 10000：表示60 秒内如果至少有 10000 个 key 的值变化，则保存
```

##### 手动触发
提供了两种命令
- save
该命令会阻塞当前Redis服务器，执行save命令期间，Redis不能处理其他命令，直到RDB过程完成为止。
- bgsave
执行该命令时，Redis会在后台异步进行快照操作，同时还可以响应客户端请求。具体操作是Redis进程执行fork操作创建子进程，RDB持久化过程由子进程负责，完成后自动结束。阻塞只发生在fork阶段，一般时间很短。
##### 对比
![eaa6b0418d701f629c40eb6aba3618b1](Redis之RDB持久化.resources/7241F4E3-2FE8-4A68-B725-1255B55A8DC4.png)

#### 恢复数据
- 将备份文件 (dump.rdb) 移动到 redis 安装目录并启动服务即可，redis就会自动加载文件数据至内存了。
- Redis 服务器在载入 RDB 文件期间，会一直处于阻塞状态，直到载入工作完成为止。
注：获取 redis 的安装目录可以使用 config get dir 命令
![02ec04e9b969264920938a8651add762](Redis之RDB持久化.resources/A97F3ED8-C7D5-463E-B95C-35D855850CF8.png)


#### 停止持久化
当只想利用Redis的缓存功能，并不像使用 Redis 的持久化功能， 可以将redis.conf 中，save 行注释掉或者直接一个空字符串`save ""`, 来停用保存功能

#### RDB自动保存原理
##### redisService结构
Redis的服务器状态，使用redisService结构保存

``` C
struct redisService{
     //1、记录保存save条件的数组
     struct saveparam *saveparams;
     //2、修改计数器
     long long dirty;
     //3、上一次执行保存的时间
     time_t lastsave;
 
}
struct saveparam{
     //秒数
     time_t seconds;
     //修改数
     int changes;
};
```
举例：
在 redis.conf 配置文件中进行了关于save 的配置，在服务器状态中的saveparam 数组将会是如下的样子：
![4d222bb5fe42c52358d7470ec490afd7](Redis之RDB持久化.resources/5E259A51-871D-4D29-BD79-B13A1B1BDF63.png)

##### dirty 计数器和lastsave 属性

　　dirty 计数器： 记录距离上一次成功执行 save 命令或者 bgsave 命令之后，Redis服务器进行了多少次修改（包括写入、删除、更新等操作）。

　　lastsave 属性： 它是一个时间戳，记录上一次成功执行 save 命令或者 bgsave 命令的时间。

-　通过这两个命令，当服务器成功执行一次修改操作，那么dirty 计数器就会加 1，而lastsave 属性记录上一次执行save或bgsave的时间。
-  Redis 服务器还有一个周期性操作函数 severCron ,默认每隔 `100 毫秒`就会执行一次，该函数会遍历并检查 saveparams 数组中的所有保存条件，只要有一个条件被满足，那么就会执行 bgsave 命令。
-　执行完成之后，dirty 计数器更新为 0 ，lastsave 也更新为执行命令的完成时间。


#### RDB文件结构
- 简要
![b50148c90f64f2528bebeb26c0c08fd2](Redis之RDB持久化.resources/201A1691-0544-4C53-8E3D-4F90303AE3F2.png)
- 详解
下面是一个 version 9 的 RDB 文件
![2ce931e146e09d42e6841582c500effb](Redis之RDB持久化.resources/36FBD139-51B0-4B9D-83AC-AF131CBA5801.png)


注：RDB文件保存的是二进制数据。

##### REDIS部分
作用：RDB文件标识符。通过这五个字符，程序可以在载入文件时，快速检查所载入的文件是否为RDB文件
长度：5字节，保存REDIS这五个字符

##### db_version部分
作用： 代表RDB文件的版本号。
长度：4字节，值是一个字符串表示的整数

##### databases部分
作用：包含0或多个数据库及其对应的键值对数据
长度：如果服务器数据库状态为空，则为0；如果不为空，则根据键值对的数量、类型和内容，长度也随之而变


##### EOF部分
作用：RDB文件结束符。标志着RDB文件正文内容的结束，读入程序遇到这个值时，代表所有数据库的所有键值对都载入完毕了
长度：1字节

##### check_sum部分
作用：检查RDB文件是否有出错或损坏。是程序通过对REDIS、db_version、databases、EOF四个部分的内容进行计算而出的；载入RDB文件时，会将载入数据所计算出的校验和与check_sum进行对比，从而得出是否出错
长度：8字节的无符号整数

#### 优势与劣势
##### 优势
1. 它保存了redis 在某个时间点上的数据集。这种文件非常适合用于进行备份和灾难恢复。
2. RDB 在恢复大数据集时的速度比 AOF 的恢复速度要快。
##### 劣势
1. 影响性能: RDB方式数据没办法做到实时持久化/秒级持久化。因为bgsave每次运行都要执行fork操作创建子进程，属于重量级操作(内存中的数据被克隆了一份，大致2倍的膨胀性需要考虑)，频繁执行成本过高。
2. 版本不兼容: RDB文件使用特定二进制格式保存，Redis版本演进过程中有多个格式的RDB版本，存在老版本Redis服务无法兼容新版RDB格式的问题。
3. 数据有丢失: 在一定间隔时间做一次备份，所以如果redis意外down掉的话，就会丢失最后一次快照后的所有修改。

#### 相关配置
```
# RDB自动持久化规则
# 当 900 秒内有至少有 1 个键被改动时，自动进行数据集保存操作
save 900 1
# 当 300 秒内有至少有 10 个键被改动时，自动进行数据集保存操作
save 300 10
# 当 60 秒内有至少有 10000 个键被改动时，自动进行数据集保存操作
save 60 10000

# RDB持久化文件名
dbfilename dump-<port>.rdb

# 数据持久化文件存储目录
dir /var/lib/redis

# bgsave发生错误时是否停止写入，通常为yes
stop-writes-on-bgsave-error yes

# rdb文件是否使用压缩格式
rdbcompression yes

# 是否对rdb文件进行校验和检验，通常为yes
rdbchecksum yes
```


> 参考：
> https://segmentfault.com/a/1190000020518214
>https://blog.csdn.net/qq_41594698/article/details/94902254

