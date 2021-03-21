---
tags: [jvm]    
categories: [Java,jvm]
---


[TOC]
> 本文是以jdk1.8的hotspot虚拟机为范例，介绍JVM的内部机制的。

## 引言

JVM主要由三个主要的子系统构成

1. 类加载机制
2. 运行时数据区（内存结构）
3. 执行引擎
![802cf3897f61649d63120d1178f0303d](JVM内部机制.resources/83E91473-6B07-4C0A-A8E0-1A27BBDC0237.png)


- 连接

验证：验证字节码文件的正确性。

准备： 给类的静态变量分配内容，并赋予默认值(jvm默认的初始值)。

解析：类装载器装入类所引用的其他所有类，即完成静态链接操作，将符号引用变为直接引用。

初始化：为类的静态变量赋予初始值(程序中的变量真正的初始值)，执行静态代码块。

注：

静态链接：解析阶段，将符号引用转化为直接引用。

动态链接：程序运行期间，将符号引用转化为直接引用。



## 类加载机制

### 全盘责任委托机制

当一个classloader加载一个Class的时候，这个Class所依赖的和引用的其它Class，通常也由这个classloader负责载入（显示指定类加载器除外）。

### 双亲委派机制

先委托父类加载器寻找目标类，只有在父类找不到时才在自己的类路径中寻找。

目的：

1. 沙箱安全机制：可以防止核心库被随意篡改。
2. 避免重复加载：保证字节码文件只被加载一次。



为什么要通过显示指定类加载器，打破双亲委派模型？

一般是因为加载花费的时间比较长，如Tomcat、JDBC、热部署等都会打破双亲委派模型。Tomcat是为了做应用间隔离，防止两个应用共用一个类信息模板，产生冲突 ；

本质：不同的ClassLoader加载相同的Class文件，会产生的不同的Class模板信息。



哪些内存需要回收？

Java使用可达性分析算法，来判定。



## 内存结构

堆：用于存放对象的实例。当对象无法在该空间申请到内存时，将抛出OOM(OutOfMemeryError)异常。

方法区：所有的定义的方法信息都保存在该区域，类的元数据（类字段 + 类方法 + 类构造方法 + 接口定义 ）+ 静态变量 + 运行时常量池。虽然jvm规范将其描述为堆的一个逻辑部分，但是它却有个别名叫Not-Heap，目的应该是为了Java的堆区分开。



方法区在jdk1.8前，hotspot虚拟机叫Permanent(永久代/持久代)，jdk1.8后，叫Metaspace(元空间)。 

改造原因：类的元数据信息转移到Metaspace的原因是PermGen很难调整。PermGen中类的元数据信息在每次FullGC的时候可能会被收集，而且应该为PermGen分配多大的空间很难确定。

jdk1.8 对 JVM 架构的改造：

1. 将类元数据从虚拟机转移到本地内存，另外，将**常量池**和**静态变量**放到 Java 堆里。 
2. HotSopt VM 将会为类元数据**明确分配和释放本地内存**。Metaspace具有动态扩容机制，它的大小会自动随着使用而动态变化。

3. jdk1.8前项目之间无法共用公有的class，改成metaSpaces后，各个项目会共享同样的class内存空间。eg：多个项目都引用了apache-common包，在metaSpaces中只会存储一份apache-common的class，提高了内存的利用率，垃圾回收更有效率。  

永久代的移除对最终用户意味着什么？ - 减少了OOM的发生

1. 类元信息就突破了原来 -XX:MaxPermSize 的限制,所以PermSize的配置也是无效的；

2. 由于类的元数据可以在本地内存(native memory)之外分配，所以其最大可利用空间是**整个系统内存的可用空间**。所以可以使用更多的本地内存。因此从一定程度上解决了原来在运行时生成大量类的造成经常 Full GC 问题。减少了OOM错误的发生，但并不意味者类加载器泄露的问题就没有了。

 

## GC

推荐：

https://www.cnblogs.com/aspirant/p/8662690.html

https://www.jianshu.com/p/30e8ff0f7dd9



#### 分代回收算法
![b160c623d1c81bca62f7f5ccc334e72d](JVM内部机制.resources/B6892837-D544-4121-941A-4915AEAB0D31.png)

Young Generation : Old Generation比例 - 1 ：2

eden:from:to比例 - 8:1:1

>  什么情况下，对象会年轻代 -> 老年代？

在年轻代中经历了N次垃圾回收(默认是15次，因为用4bit来存储；可以调整)后仍然存活的对象，就会被放到年老代中。 

 当survivor1区不足以存放 eden和survivor0的存活对象时，就将存活对象直接存放到老年代。



#### GC类别

**Scavenge GC/Minor GC/YoungGC** ： 当新对象生成并且在Eden申请空间失败时，清理Eden区和Survivor区；先对Eden区域进行GC ，清除非存活对象，并且把尚且存活的对象移动到Survivor区。 然后整理Survivor的两个区。发生频率比较高(不一定等Eden区满了才触发)。

**CMS OldGC**: CMS垃圾收集器才会产生，清理老年代。

**Major GC/Full GC**：清理整个堆空间（包括年轻代和老年代）和元空间

**G1 Mixed GC **：G1垃圾收集器的混合GC算法



#### GC调优指标 

jvm调优，主要调整的指标：

- 停顿时间：垃圾回收期做垃圾回收中断应用执行的时间。 -XX:MaxGCPauseMills
- 吞吐量：垃圾收集时间和总时间的占比,  吞吐量=1-  1/(1+n)。-XX:GCTimeRatio=n

需要针对项目业务类型，来调整。



#### GC调优步骤 

> 参考: https://blog.csdn.net/CoderBruis/article/details/101234738

1. 添加启动参数，打印GC日志

   ```
   //将GC日志保存在当前目录gc.log文件中
   -XX:+PrintGCDetails -XX:PrintGCTimesStanmps -XX:+PrintGCDateStamps -Xloggc:./gc.log
   ```

   注：Tomcat可以直接加在JAVA_OPTS变量里

2. 分析日志得到关键性指标，这里可以借助如jvisualvm等工具。

   推荐-在线GC分析网站:https://www.gceasy.io/

3. 分析GC原因，调优jvm参数。

   eg: 
   设置元空间初始化和最大空间大小： -XX:MetaspaceSize=128M -XX:maxMetaspaceSize=128

   增加年轻待动态扩容增量(默认是20%)，可以减少YoungGC：-XX：YoungGenerationSizeIncrement=30









