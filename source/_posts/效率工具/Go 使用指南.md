---
title: Go 使用指南
tags: [go]
categories: [效率工具]
date: 2021-10-21
cover: https://contentstatic.techgig.com/photo/82278297/5-top-advantages-of-using-golang-programming-language.jpg?35743
---

入门脑图：https://www.processon.com/mindmap/5ea549685653bb6efc6e4201
高阶脑图：https://www.processon.com/mindmap/60673b831e08534321f88c0c

# 下载&安装

## 可以指定安装版本

```
go get github.com/someone/some_module@{YOUR_GIT_COMMIT_HASH}
```

eg: go get gitlab.pri.ibanyu.com/server/projectmanager/pub.git@master

[Go 语言多版本管理利器 GVM](https://www.hi-linux.com/posts/20165.html#gvm)

## mac下设置gopath环境变量

- [官方指导](https://github.com/golang/go/wiki/SettingGOPATH)
- Bash

编辑~/.bash_profile文件，添加以下代码

```
export GOROOT=/usr/local/Cellar/go/1.10.3/libexec

export GOPATH=/Users/chenxingyi/work/go

export GOBIN=

export PATH=$PATH:${GOPATH//://bin:}/bin

123456789
```

保存，然后执行

```
source ~/.bash_profile
```

- Zsh

编辑~/.zshrc文件，添加以下代码

```
export GOROOT=/usr/local/Cellar/go/1.10.3/libexec

export GOPATH=/Users/chenxingyi/work/go

export GOBIN=

export PATH=$PATH:${GOPATH//://bin:}/bin

123456789
```

保存，然后执行

```
source ~/.zshrc
```

#### 问题：GOPATH设置不生效

- 正常情况下个以上执行完之后，执行`go env` 就能看见自己设置的环境变量了，然而事实却并非如此

我就碰到无论我怎么设置，最后执行source ~/.zshrc 之后环境变量一直是go安装时默认的

```
GOPATH=/Users/Chenxingyi/go
```

脑洞想了一下：
-. 是不是我配置的环境变量方式不对？
-. 或者配置的地方不对？
-. 或者其他什么地方也配置了相同的环境变量？

前面两个方法验证了都没问题，最后grep搜索了一下当前什么地方配置了这些GOPATH，提示"GOROOT and GOPATH are set automatically" 猜想可能是这里导致的，一看前面gvm，想到了当时安装过gvm，gvm是管理电脑上多个版本go的工具，但是就在这个工具会在

**.bash_profile**和 **.zshrc**文件的末尾加上了一段代码：

```
[[ -s "/Users/ryan/.gvm/scripts/gvm" ]] && source "/Users/ryan/.gvm/scripts/gvm"
```

最后想到把GVM卸载看看效果，果不其然，卸载完就好了，我们设置的GOPATH生效了

- [如何卸载GVM](https://github.com/moovweb/gvm/issues/285)

a. `rm -rf ~/.gvm`

b. 删除**.bash_profile**和 **.zshrc**文件的末尾加上的一段代码：

```
[[ -s "/Users/ryan/.gvm/scripts/gvm" ]] && source "/Users/ryan/.gvm/scripts/gvm"
```

# 使用

## 基础原理

### [参数传递到底是传值还是传引用](https://blog.csdn.net/qq_39397165/article/details/109561839)

兄弟们实锤了奥，go就是值传递，可以确认的是Go语言中所有的传参都是值传递（传值），都是一个副本，一个拷贝。因为拷贝的内容有时候是非引用类型（int、string、struct等这些），这样就在函数中就无法修改原内容数据；有的是引用类型（指针、map、slice、chan等这些），这样就可以修改原内容数据。

是否可以修改原内容数据，和传值、传引用没有必然的关系。在C++中，传引用肯定是可以修改原内容数据的，在Go语言里，虽然只有传值，但是我们也可以修改原内容数据，因为参数是引用类型。

有的小伙伴会在这里还是懵逼，因为你把引用类型和传引用当成一个概念了，这是两个概念，切记！！！

### Json 解析

[Go的json解析:Marshal与Unmarshal](https://cloud.tencent.com/developer/article/1515861)

### 接口压测

[adjust/go-wrk](https://github.com/adjust/go-wrk)

```
./go-wrk  -c 10   -m "POST"  -b '{"version":1,"encoding":"command","command":"SET","namespace":"test/test","prefix":"indexer","payload_data":[["golden_k1","v1",120],["golden_k2","v2",120],["golden_k3","v3",120],["golden_k4","v4",120],["golden_k5","v5",120]]}'  -H 'Authorization: prn=prn:pf-cn:cache:hz::redis,action=cache:SET,token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6MTU5NjIwNzk4NH0.eyJpc3MiOiJJQU0iLCJzdWIiOiJncm91cCBjSEpMd1BId1VEckpPN2gvaWtZd2Z3PT0ifQ.2QCY70txMc2gSaHKRz59gAfdxRYoVuz8_Xg681YIq8Q; Content-Type: application/json; ' -n 10000 http://10.92.197.49:40465/base/indexer/cache/data/add

```

## goroutine & channel

> Go 语言为构建并发程序的基本代码块是 协程 (goroutine) 与通道 (channel)。
> 多线程下，如何实现对共享变量的正确访问需要精确的控制？
> 主要是要解决内存中的数据共享问题。

1.  对数据加锁，这样同时就只有一个线程可以变更数据。 - Go 的标准库 `sync`有工具类
2.  它将共享的值通过信道传递，这样可以无需提供同步原语。 即：`不要通过共享内存来通信，而应通过通信来共享内存。`注：**不要使用全局变量或者共享内存，它们会给你的代码在并发运算的时候带来危险。**第二种模式对比第一种模式而言，不但具有性能优势，而且代码显得更清晰、更优雅。

扩展：Go 将共享的值通过信道传递。实际上，多个独立执行的线程从不会主动共享。 在任意给定的时间点，只有一个 Go 协程能够访问该值。 并不存在竞争关系，对一个通道读数据和写数据的整个过程是原子性的。

### Master-Worker 问题

一个类似于 worker 使用通道进行通信和交互、Master 进行整体协调的方案都能完美解决。

```go
func main() {
  pending, done := make(chan *Task), make(chan *Task)
  go sendWork(pending)       // put tasks with work on the channel
  for i := 0; i < N; i++ {   // start N goroutines to do work
    go Worker(pending, done)
  }
  consumeWork(done)          // continue with the processed tasks
}

//从 pending 通道拿任务，处理后将其放到 done 通道中
func Worker(in, out chan *Task) {
  for {
    t := <-in
    process(t)
    out <- t
  }
}



```

**怎么选择是该使用锁还是通道**

使用锁的情景：

- 访问共享数据结构中的缓存信息
- 保存应用程序上下文和状态信息数据

使用通道的场景：

- 分发任务

- 传递数据所有权

- 与异步操作的结果进行交互

### goroutine 协程

#### 定义

它是与其它 Go 协程并发运行在同一地址空间的函数。即：协程工作在相同的地址空间中。

#### 与线程的关系

在协程和操作系统线程之间并无一对一的关系：协程是根据一个或多个线程的可用性，多路复用在他们之上执行的；

协程可以运行在多个操作系统线程之间，也可以运行在线程之内

#### 特点

它是轻量级的， 所有消耗几乎就只有栈空间的分配，且协程的栈会根据需要进行伸缩，不会出现栈溢出；

Go 协程在多线程操作系统上可实现多路复用；

Go 协程的设计隐藏了线程创建和管理的诸多复杂性；

#### 使用

在函数或方法前添加 `go` 关键字能够在新的 Go 协程中调用它。当调用完成后， 该 Go 协程也会安静地退出。

#### 设置GOMAXPROCS

GOMAXPROCS的数值代表允许运行时支持使用多少个的操作系统线程，默认为1；即：GOMAXPROCS 等同于（并发的）线程数量

通常，如果有 `n` 个核心，会设置 `GOMAXPROCS` 为 `n-1` 以获得最佳性能，但同样也需要保证，

`协程的数量 > 1 + GOMAXPROCS > 1`

注：

当 `GOMAXPROCS` 等于 `1` 时，所有的`协程`都会共享同一个`线程`。
当 `GOMAXPROCS` 大于 `1` 时，会有一个线程池管理众多线程。

只有 gc 编译器真正实现了协程，适当的把协程映射到操作系统线程。使用 `gccgo` 编译器，会为每一个协程创建操作系统线程。

#### Go的协程 和 （其他语言的）协程的区别

    1. Go 协程意味着并行（或者可以以并行的方式部署），协程一般来说不是这样的
    2. Go 协程通过通道来通信，协程通过让出和恢复操作来通信

### channel 信道/通道

> 通道实际上是类型化消息的队列：使数据得以传输。

#### 作用： 同步协程；

#### 使用

声明格式：`var identifier chan datatype` // 通道只能传输一种类型的数据

通道是引用类型，通过 `make` 来分配内存。

```go
ci := make(chan int)            // 整数无缓冲信道
cj := make(chan int, 0)         // 整数无缓冲信道
cs := make(chan *os.File, 100)  // 指向文件的指针的缓冲信道
```

举例：

```go
c := make(chan int)  // 创建一个无缓冲的类型为整型的 channel 。
//用 goroutine 开始排序；当它完成时，会在信道上发信号。
go func() {
    list.Sort()
    c <#### 1  // 发送一个信号，这个值并没有具体意义
}()
doSomethingForAWhile()
<-c   // 等待 sort 执行完成，然后从 channel 取值
```

#### 状态与操作

channel存在`3种状态`：

1. nil，未初始化的状态，只进行了声明，或者手动赋值为`nil`
2. active，正常的channel，可读或者可写
3. closed，已关闭，**千万不要误认为关闭channel后，channel的值是nil**

channel可进行`3种操作`：

1. 读
2. 写
3. 关闭

![5e38af5027db9c32400012aede8e922c.png](evernotecid://CD3082B6-03A3-4D41-80AB-E48CAD259C0B/appyinxiangcom/17782910/ENResource/p1441)

#### 发送接收机制

接收者在收到数据前会一直阻塞。

    1. 若信道是不带缓冲的，那么在接收者收到值前， 发送者会一直阻塞； #### 一个无缓冲通道只能包含 1 个元素，是一个同步队列

    2. 若信道是带缓冲的，则发送者仅在值被复制到缓冲区前阻塞； 若缓冲区已满，发送者会一直等待直到某个接收者取出一个值为止。 #### 缓冲满载（发送）或变空（接收）之前通信不会阻塞

#### 特性

等值，它可以被分配并像其它值到处传递。 这种特性通常被用来实现安全、并行的多路分解。

(即：也可以作为函数的参数传递，从函数返回以及通过通道发送它们自身）

- 使用 select 切换协程

select 做的就是：选择处理列出的多个通信情况中的一个。

如果都阻塞了，会等待直到其中一个可以处理
如果多个可以处理，随机选择一个
如果没有通道操作可以处理并且写了 default 语句，它就会执行：default 永远是可运行的（这就是准备好了，可以执行）。

- 周期请求、超时检测 - 结合定时器Timer
- 限制处理频率 - 结合计时器 Ticker
- 信号量

扩展：
[channel用法总结](https://segmentfault.com/a/1190000017958702?utm_campaign=studygolang.com&utm_medium=studygolang.com&utm_source=studygolang.com)
