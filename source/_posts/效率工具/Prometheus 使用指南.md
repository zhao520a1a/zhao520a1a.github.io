---
title: Prometheus 使用指南
tags: [prometheus]   
categories: [效率工具]
date: 2020-11-01
cover: https://sysdig.com/wp-content/uploads/Blog-Kubernetes-Monitoring-with-Prometheus-1-Featured-image.png
---



## 引言
### 相关概念
**TSDB**：时序数据库 是数据库大家庭中的一员，专门存储随时间变化的数据；

**时序 (Time Series)** 指的是某个变量随时间变化的所有历史；每个时序由一个名字(Metric)和一组**标签** (labels) 标识定义。

**样本 (Sample)** 指的是历史中该变量的瞬时值；每个样本由**时序标识**、**时间戳**(一个毫秒级的 unix 时间戳)、**数值** (float64 值) 3 部分构成

<img src="Prometheus%20%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/auto-orient,1.jpeg" alt="img" />



> 时序是如何被定义的？

### 时序格式 

每个时序由一个名字(Metric)和一组**标签** (labels) 标识定义的。（时序名字本质上就是一个隐藏标签）。

`<metric name>{<label name>=<label value>, ...}`

``` bash
# 该时序的名字为 api_http_requests_total，标签为 path、status、method 和 instance
api_http_requests_total{path="/users",status=200,method="GET",instance="10.111.201.26"}
```

只有时序名字和标签键值完全相同的时序才是同一个时序。

##### Metric命名

 要表示metric的功能，如`http_request_total`。时序的名字由 ASCII 字符，数字，下划线，以及冒号组成，它必须满足正则表达式 [a-zA-Z_:][a-zA-Z0-9_:]*, 其名字应该具有语义化，一般表示一个可以度量的指标，例如 http_requests_total, 可以表示 http 请求的总数。

##### Metric类型

- `Counter`: 一种累加的`metric`，如请求的个数，结束的任务数，出现的错误数等
- `Gauge`: 常规的metric,如温度，可任意加减。其为瞬时的，与时间没有关系的，可以任意变化的数据。
- `Histogram`: 柱状图，用于观察结果采样，分组及统计，如：请求持续时间，响应大小。其主要用于表示一段时间内对数据的采样，并能够对其指定区间及总数进行统计。**根据统计区间计算**
- `Summary`: 类似`Histogram`，用于表示一段时间内数据采样结果，其直接存储quantile数据，而不是根据统计区间计算出来的。**不需要计算，直接存储结果**

## Prometheus
### 介绍
> Prometheus 是一个开源监控报警系统和时序列数据库(TSDB)，使用Go语言开发。

#### 特点
多维度数据模型。
灵活的查询语言。
不依赖分布式存储，单个服务器节点是自主的。
通过基于HTTP的pull方式采集时序数据。
可以通过中间网关进行时序列数据推送。
通过服务发现或者静态配置来发现目标服务对象。
支持多种多样的图表和界面展示，比如Grafana等。

#### 基本原理
通过`HTTP协议周期性抓取被监控组件的状态`，任意组件只要提供对应的HTTP接口就可以接入监控。非常适合做虚拟化环境监控系统，比如VM、Docker、Kubernetes等。

exporter：输出被监控组件信息的HTTP接口
metrics: 指标

#### 服务过程
- Prometheus采用PULL的方式进行监控，在本地存储抓取的所有数据，并通过一定规则进行清理和整理数据，并把得到的结果存储到新的时间序列中。
- Prometheus通过PromQL和其他API可视化地展示收集的数据。
- PushGateway支持Client主动推送metrics到PushGateway，而Prometheus只是定时去PushGateway上抓取数据。
- Alertmanager是独立于Prometheus的一个组件，提供十分灵活的报警方式。

#### 三大套件
Server 主要负责数据采集和存储，提供PromQL查询语言的支持。
Alertmanager 警告管理器，用来进行报警。
PushGateway 支持临时性Job主动推送指标的中间网关。


### 架构图
<img src="Prometheus%20%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/CF48A9A4-208F-4302-9FD1-1F7F7213DA65.png" alt="img" />


### 安装使用
> 安装教程: [从零搭建Prometheus监控报警系统](https://www.cnblogs.com/chenqionghe/p/10494868.html)
[Prometheus](http://47.93.119.45:9090/targets)
[Pushgateway](http://47.93.119.45:9091/#)
[Grafana](http://47.93.119.45:3000/#)
[AlertManager](http://47.93.119.45:9093/#/alerts)


- 热加载配置文件
``` bash
curl -X POST http://localhost:9090/-/reload
```

#### 建立相应文件夹
``` bash
mkdir -p /home/promethues
mkdir -p /home/promethues/server
mkdir -p /home/promethues/client
touch /home/promethues/server/rules.yml
chmod 777 /home/promethues/server/rules.yml
```


#### 安装Prometheus-Server

- 配置
``` bash
global:
  scrape_interval:     15s # 默认抓取间隔, 15秒向目标抓取一次数据。
  external_labels:
    monitor: 'codelab-monitor'
# 这里表示抓取对象的配置
scrape_configs:
    #这个配置是表示在这个配置内的时间序例，每一条都会自动添加上这个{job_name:"prometheus"}的标签  - job_name: 'prometheus'
    scrape_interval: 5s # 重写了全局抓取间隔时间，由15秒重写成5秒
    static_configs:
      - targets: ['localhost:9090']
```
- docker启动
``` bash
docker rm -f prometheus
docker run --name=prometheus -d \
-p 9090:9090 \
-v /home/chenqionghe/promethues/server/prometheus.yml:/etc/prometheus/prometheus.yml \
-v /home/chenqionghe/promethues/server/rules.yml:/etc/prometheus/rules.yml \
prom/prometheus:v2.7.2 \
--config.file=/etc/prometheus/prometheus.yml \
--web.enable-lifecycle
```

- 访问
``` bash
http://localhost:9090
```
<img src="Prometheus%20%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/7EB0113A-5D55-4D1A-92B8-3E64B2923A04.png" alt="img" />


#### 推送指标
``` bash
cat <<EOF | curl --data-binary @- http://47.93.119.45:9091/metrics/job/cqh/instance/test
# 锻炼场所价格
muscle_metric{label="gym"} 8800
# 三大项数据 kg
bench_press 100
dead_lift 110
deep_squal 180
EOF
```



#### 安装Pushgateway

<img src="Prometheus%20%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/C1BA5F68-0915-45C0-A15A-D447F1E31B72.png" alt="img" />



#### 安装Grafana
<img src="Prometheus%20%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/64D6059D-F4CC-4A51-83F2-66C02016B5F6.png" alt="img" />


#### 安装Altermanager
> - Grafana是用于可视化大型测量数据的开源程序，它提供了强大和优雅的方式去创建、共享、浏览数据。
> -Grafana最常用于因特网基础设施和应用分析，但在其他领域也有用到，比如：工业传感器、家庭自动化、过程控制等等。

<img src="Prometheus%20%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97/B960EF6A-CE6D-4F7C-841B-85FCC0D915B2.png" alt="img" />
> 注：默认登录账户和密码都是admin

## PromQL 

> 查询时序：
> count({__name__ =~ "indexer_metrics_app_.*"})

>  [prometheus promql查询表达式](https://www.cnblogs.com/ZhongzhouChen/p/11696792.html)
>  [prometheus-book](https://yunlzheng.gitbook.io/prometheus-book/parti-prometheus-ji-chu/promql/prometheus-metrics-types)


PromQL (Prometheus Query Language) ，这是Prometheus开发的数据查询DSL语言，日常的可视化以及告警规则都要用到它。

### 基础语法

#### 文字类型

**字符串值**

用单引号、双引号、反引号(不做任何转义处理)表示。

PromQL遵循与Go相同的转义规则。

单引号和双引号，用反斜杠开始一个转义序列。

反引号内不会处理任何转义， 但与Go不同，Prometheus不会在反引号内丢弃换行符。

``` bash
"this is a string"
'these are unescaped: \n \\ \t'
`these are not unescaped: \n ' " \t`
```

**浮点值**

``` bash
-2.43
```

#### 注释

``` bash
# 这是一段注释
```



> 如何查询时序？

#### 查询条件(时序选择器)

通过名称及标签进行查询。可以通过在{}使用标签匹配器列表，来过滤时间序列；

注：由于时序名字本质上就是一个隐藏标签，因此也可以通过内部`_name_`标签进行匹配。

``` bash
http_requests_total
等价于： {_name_=“ http_requests_total”}
```

``` bash
http_requests_total{job="prometheus",group="canary"} 
```

**标签匹配运算符**

- =：选择与提供的字符串完全相等的标签。

- ！=：选择不等于提供的字符串的标签。

- =〜：选择与提供的字符串进行正则表达式匹配的标签。

- ！〜：选择不与提供的字符串正则表达式匹配的标签。

``` bash
# 查询条件支持正则匹配
http_requests_total{code!="200"}  // 表示查询 code 不为 "200" 的数据
http_requests_total{code=~"2.."} // 表示查询 code 为 "2xx" 的数据
http_requests_total{code!~"2.."} // 表示查询 code 不为 "2xx" 的数据
http_requests_total{environment=~"staging|testing|development",method!="GET"}
```

``` bash
# 以下表达式选择名称以job开头的所有时序
{_name_=~"job:.*"}
```



> 如何判定标签选择器列表是否合法？

查询语句规则：必须指定一个名称或至少一个与空字符串不匹配的标签匹配器。 

``` bash
{job=~".*"} 						 # Bad! 同空字符串匹配
{job=~".+"}              # Good!
{job=~".*",method="get"} # Good!
```



#### Offset 修饰符

offset修饰符允许更改查询中各个瞬时矢量和范围矢量的时间偏移。

``` bash
# 返回相对于当前查询评估时间过去5分钟的http_requests_total值：
http_requests_total offset 5m
# 返回http_requests_total一周前的5分钟费率：
rate(http_requests_total[5m] offset 1w)
```

offset修饰符必须始终需要立即跟随选择器。

```  bash
sum(http_requests_total{method="GET"} offset 5m) // GOOD.
sum(http_requests_total{method="GET"}) offset 5m // INVALID.
```



#### 查询表达式类型

- 瞬时向量表达式 (Instant vector): 包含一组时序，每个时序只有一个点，例如：`http_requests_total` 即：选择出给定的时间戳（即时）上的一组时间序列和单个样本值
- 区间向量表达式 (Range vector): 包含一组时序，每个时序有多个点，例如：`http_requests_total[5m]`
- 纯量表达式 (Scalar): 纯量只有一个数字，没有时序，例如：`count(http_requests_total)`
- String-一个简单的字符串值；目前未使用

#### 子查询

子查询的结果是区间向量表达式。

`<instant_query> [ <range> ：[<resolution>] ] [offset <持续时间>]`

注：<resolution>是可选的。 默认值为全局评估间隔。

### 操作符

Prometheus 查询语句中，支持常见的各种表达式操作符。

**算术运算符**:

支持的算术运算符有 `+，-，*，/，%，^`

在两个scalar操作数之间，结果是另一个scalar数据；

在vector操作数和scalar操作数之间，会将运算符应用于vector中每个数据样本的值，结果是另一个vector数据。

``` bash
# 将 http_requests_total 所有数据 double 一倍， 每个样本都乘以2
http_requests_total * 2
```

在两个vector操作数之间，将运算符应用于左侧vector中的每个条目和右侧vector中匹配元素。结果是另一个vector数据，并且分组标签成为输出标签集。  

注： 在右侧vector中找不到匹配条目的条目不属于结果。

**比较运算符**:

支持的比较运算符有 `==，!=，>，<，>=，<=`, 用于过滤数据

``` bash
# http_requests_total 结果中大于 100 的数据
http_requests_total > 100
```

**逻辑运算符**:

支持的逻辑运算符有 `and，or，unless`, 只能在两个瞬时向量表达式之间使用。

- **vector1 and vector2** 产生一个以vector1为基础交集。结果向量名称和值从vector1继承。 

- **vector1 or vector2** 产生一个并集向量，其中包含vector1的所有原始元素（标签集+值），以及在vector1中没有匹配的标签集的vector2的元素。

- **vector1 unless vector2**，产生一个以vector1为基础的数据补集。 两个向量中的所有匹配元素都将被删除。

``` bash
#  http_requests_total 结果中等于 5 或者 2 的数据
http_requests_total == 5 or http_requests_total == 2
```

**分组修饰符**：

使用group_left或group_right 确定哪个向量具有更高的基数，即：谁是“多”的那侧

分组修饰符只能用于比较和算术。



**聚合运算符**:

可用于聚合单个瞬时向量的元素，从而产生具有聚合值的较少元素的新向量：

支持的聚合运算符有 `sum，min，max，avg，stddev，stdvar，count，count_values，bottomk，topk，quantile `

``` bash
max(http_requests_total)   # 表示 http_requests_total 结果中最大的数据
sum(http_requests_total)  
count_values("version", build_version)
topk(5, http_requests_total)
```

格式：

`<aggr-op> [without|by (<label list>)] ([parameter,] <vector expression>)`

or 

`<aggr-op>([parameter,] <vector expression>) [without|by (<label list>)]`

说明：

- label list : 标签列表，以逗号分隔，（label1，label2）和（label1，label2，）均为有效语法。

- without | by   : without是从结果向量中删除列出的标签，by是从结果中只保留列出的标签
- parameter: 只能在count_values, quantile, topk, bottomk使用

特别说明：

- count_values  : 相同值元素的数量，每个唯一样本值输出一个时间序列。  每个时间序列的值是样本值出现的次数。
- quantile   : 分位数计算， eg: 中位数quantile(0.5，...)，95分位，quantile(0.95, ...)

-  topk ，bottomk :  样本值最大、最小的k个元素，将输入样本的一个子集（包括原始标签）返回到结果向量中，此时by和not仅用于存储输入向量，



**运算符优先级**

优先级由高到低如下：

1. `^`
2. `*`, `/`, `%`
3. `+`, `-`
4. `==`, `!=`, `<=`, `<`, `>=`, `>`
5. `and`, `unless`
6. `or`

优先级相同的运算符是左关联的。 

```  bash
2 * 3 ％ 2   等价于 （2 * 3）％2。
2 ^ 3 ^ 2   等效于  2 ^（3 ^ 2）  # 这是由于^是右联想
```



#### 数据匹配

数据之间运算，尝试在左侧数据中，为每个样本找到匹配的元素。

匹配类型

**一对一**

格式： `vector1 <operator> vector2`

如果两个条目具有完全相同的一组标签和相应的值，则它们匹配。 

ignoring关键字允许在匹配时忽略某些标签

on关键字允许将考虑的标签集减少到提供的列表中

`<vector expr> <bin-op> ignoring(<label list>) <vector expr>`

`<vector expr> <bin-op> on(<label list>) <vector expr>`

**多对一/一对多**

将“一个”侧的每个矢量元素都可以与“许多”侧的多个元素匹配

**分组修饰符**

必须使用group_left或group_right修饰符明确地请求它，其中left / right确定哪个向量具有更高的基数。

`<vector expr> <bin-op> ignoring(<label list>) group_left(<label list>) <vector expr>`

`<vector expr> <bin-op> ignoring(<label list>) group_right(<label list>) <vector expr>`

`<vector expr> <bin-op> on(<label list>) group_left(<label list>) <vector expr>`

`<vector expr> <bin-op> on(<label list>) group_right(<label list>) <vector expr>`

举例：

``` bash
method_code:http_errors:rate5m{method="get", code="500"}  24
method_code:http_errors:rate5m{method="get", code="404"}  30
method_code:http_errors:rate5m{method="put", code="501"}  3
method_code:http_errors:rate5m{method="post", code="500"} 6
method_code:http_errors:rate5m{method="post", code="404"} 21

method:http_requests:rate5m{method="get"}  600
method:http_requests:rate5m{method="del"}  34
method:http_requests:rate5m{method="post"} 120


method_code:http_errors:rate5m{method="get",code="500"} / ignoring(code) method:http_requests:rate5m  0.04 = 24 / 600
method_code:http_errors:rate5m{method="post",code="500"} / ignoring(code) method:http_requests:rate5m   0.05 =  6 / 120
```



``` bash
# 左侧为“多的”的那侧，右侧的元素与左侧具有相同方法标签的多个元素匹配；
method_code:http_errors:rate5m {method="get", code="500"}  / ignoring(code) group_left method:http_requests:rate5m  0.04  =  24 / 600

method_code:http_errors:rate5m {method="get", code="404"}  / ignoring(code) group_left method:http_requests:rate5m   0.05  =  30 / 600

method_code:http_errors:rate5m {method="post", code="500"}  / ignoring(code) group_left method:http_requests:rate5m    0.05  =   6 / 120

method_code:http_errors:rate5m {method="post", code="404"} / ignoring(code) group_left method:http_requests:rate5m   0.175  =  21 / 120

```

注：多对一和一对多匹配使用的不太多，谨慎考虑使用。

### 基本查询

1. 查询当前所有数据

``` bash
logback_events_total 
```

2. 模糊查询： level="inxx"

``` bash
logback_events_total{level=~"in.."}

logback_events_total{level=~"in.*"}
```

3. 比较查询： value>0

``` bash
logback_events_total > 0
```

4. 范围查询： 过去5分钟数据

``` bash
logback_events_total[5m]
```

- 时间范围单位有以下：
  - **`s`**: 秒
  - **`m`**: 分钟
  - **`h`**: 小时
  - **`d`**: 天
  - **`w`**: 周
  - **`y`**: 年

在瞬时向量表达式或者区间向量表达式中，都是以当前时间为基准。

如果想查询5分钏前的瞬时样本数据，则需要**使用位移操作**，关键字：**`offset`**, 其要紧跟在选择器`{}`后面。如：

```bash
sum(http_requests_total{method="GET"} offset 5m)

rate(http_requests_total[5m] offset 1w) 
```



###内置函数

> Prometheus 内置不少函数，方便查询以及数据格式化，

- 将浮点数转换为整数

``` bash
# 将结果由浮点数转为整数的 floor 和 ceil，
floor(avg(http_requests_total{code="200"}))
ceil(avg(http_requests_total{code="200"}))
```

- 查看每秒数据 ：

``` bash
# 查看 http_requests_total 5分钟内，平均每秒数据
rate(http_requests_total[5m])
```

| 函数名                                  |                                                              |
| --------------------------------------- | ------------------------------------------------------------ |
| abs(v instant-vector)                   | 取结果数据的绝对值                                           |
| absent(v instant-vector)                | 瞬时向量表达式有数据，返回空；无数据，返回1；eg: 判断指标为空时使用 |
| absent_over_time(v range-vector)        | 区间向量表达式有数据，返回空；无数据，返回1；eg: 判断指标为空时使用 |
| floor(v instant-vector)                 | 将结果由浮点数转为整数，向下取整                             |
| ceil(v instant-vector)                  | 将结果由浮点数转为整数，向上取整                             |
| changes(v range-vector)                 | 在提供的时间范围内变化的次数作为瞬时向量表达式               |
| clamp_max(v instant-vector, max scalar) | 设置结果上限最大值                                           |
| clamp_min(v instant-vector, min scalar) | 设置结果下限最小值                                           |




### 告警规则

 比如单台Nginx active指标超过1w就要发出告警， 

``` bash
nginx_http_connections{instance="172.18.11.192:9145",state="active"} > 10000
```

完整的告警规则如下：

```yaml
#group:定义一组相关规则
#alert：告警规则名称
#expr：基于PromQL的触发条件
#for 等待评估时间
#label 自定义标签
#annotation： 指定一组附加信息Alertmanger特性
groups:
 - name: Nginx
   rules:
   - alert: HighErrorRate
     expr: nginx_http_connections{instance="172.18.11.192:9145",state="active"} > 10000
     for: 5m
     labels:
       severity: page
     annotations:
       summary: "啊啊啊啊啊,(instance {{ $labels.instance }}) 连接数超1w了"
       description: "Nginx 连接数现在 VALUE = {{ $value }}\n  LABELS: {{ $labels }}"

```



>查询所用的时间戳

运行查询时，将选择**采样数据的时间戳**，而不依赖于实际的当前时间序列数据。 这主要是为了支持诸如聚合（求和，平均等）的情况，其中多个聚合时间序列未在时间上精确对齐。由于它们的独立性，Prometheus需要为每个相关时间序列在那些时间戳上分配一个值。因此，**只需在此时间戳之前获取最新样本即可**。

>  避免慢查询和重载

- 在对未知数据构建查询时，先在Prometheus表达式浏览器的表格视图中构建查询，直到结果集看起来合理为止，在切换到图形模式。避免对其进行图形化处理可能会超时或使服务器或浏览器超载。。

- 另外，即使输出只是少量时间序列，在许多时间序列上聚合的表达式也会在服务器上产生负载。 类似于将关系数据库中的列的所有值相加会很慢，即使输出值只是一个数字也是如此。
- 最多数支持百个时间序列，而不是数千个。  


> 检查prometheus.yml配置是否有效? - promtool prometheus附带了一个check config命令

**检查配置**

```bash
./promtool check config prometheus.yml 
```

正常返回状态

```bash
Checking prometheus.yml
  SUCCESS: 1 rule files found

Checking alert_rules.yml
  SUCCESS: 29 rules found
```

错误返回状态

``` bash
Checking prometheus.yml
  FAILED: parsing YAML file prometheus.yml: yaml: line 148: did not find expected key
```

### 生成式 PromQL
#### 参考项目

- 采用链式编程模式
  https://blog.csdn.net/sinat_26682309/article/details/90301904
  https://studygolang.com/articles/15134

- https://github.com/langhuihui/RxGo

- https://github.com/caunt/PromQL.NET

#### 解析PromQL 为对象
https://github.com/VictoriaMetrics/metricsql



## 参考
[官方英文文档](https://prometheus.io/docs/prometheus/latest/querying/basics/)
[官方中文文档](https://prometheus.fuckcloudnative.io/di-san-zhang-prometheus/di-4-jie-cha-xun/functions)
[安装 Promethues](https://www.cnblogs.com/chenqionghe/p/10494868.html)
[Prometheus PormQL语法及告警规则写法](https://www.icode9.com/content-4-721329.html)
