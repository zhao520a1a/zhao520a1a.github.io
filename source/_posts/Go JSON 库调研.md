---
title: Go JSON 库调研
tags: [go]
categories: [源码解读]
---

# 引言

Go 标准库 [encoding/json](https://pkg.go.dev/encoding/json) 已经是提供了足够舒适的 JSON 处理工具，广受 Go 开发者的好评。它还能有什么问题？什么情况下使用第三方库？有哪些热门的三方库？如何选型？性能如何？

| 专业术语                            | 名词解释                                                        |
| ----------------------------------- | --------------------------------------------------------------- |
| Sonic                               | 字节开源的高性能的 JSON 库                                      |
| Sonnet                              | 个人开发开发 JSON 库， ps:宣称比 Sonic 性能还高                 |
|                                     |                                                                 |
| asm(Assembly language)              | 汇编语言                                                        |
| Plan9                               | Go 底层使用的汇编是 plan9 汇编，plan9 是一个全新的 Unix 系统    |
| ast(Abstract Syntax Tree)           | 抽象语法树                                                      |
| SIMD(Single-Instruction-Multi-Data) | 单指令流多数据流，一组特殊的 CPU 指令，用于矢量数据的并行处理。 |
|                                     |                                                                 |
| lazy-load                           | 按需加载                                                        |
| buffer-reuse                        | 复用缓存区                                                      |
| JIT                                 | 即时编译                                                        |
| code-gen                            | 代码生成                                                        |
| Clang                               | 一个 C/C++/Objective C/Objective C++的轻量级编译器              |

## 你真的了解 JSON 处理吗？

```go
	var s string
	err := json.Unmarshal([]byte(`"Hello, world!"`), &s)
	assert.NoError(t, err)
	fmt.Println(s)
```

```go
	cert := struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}{}
	err = json.Unmarshal([]byte(`{"UserName":"root","passWord":"123456"}`), &cert)
	if err != nil {
		fmt.Println("err =", err)
	} else {
		fmt.Println("username =", cert.Username)
		fmt.Println("password =", cert.Password)
	}
```

测试 Demo：https://gitpod.io/#https://github.com/zhao520a1a/go-base

## 标准库有什么问题？

Go JSON 标准库大量使用反射获取值，首先 Go 的反射本身性能较差，较耗费 CPU 配置；其次频繁分配对象，也会带来内存分配和 GC 的开销；同时没有提供按需加载机制，出于**适用服务场景和降本收益的需求。**

# 调研思路

## 评判标准

性能方面，json 导致的 GC 与 CPU 压力较大，如：是否使用反射；

功能灵活性：是否支持 Unmarshal 到 map 或 struct，是否提供的一些定制化抽取的 API；

稳定性：业务较为重要，需要一个稳定的序列化库；

## 使用方式

根据主流 JSON 库 API，将它们的使用方式分为三种：

**泛型（generic）编解码**：JSON 没有对应的 schema，只能依据自描述语义将读取到的 value 解释为对应语言的运行时对象，例如：JSON object 转化为 Go map[string]interface{}；

**定型（binding）编解码**：JSON 有对应的 schema，可以同时结合模型定义（Go struct）与 JSON 语法，将读取到的 value 绑定到对应的模型字段上去，同时完成数据解析与校验；

**查找（get）& 修改（set）**：指定某种规则的查找路径（一般是 key 与 index 的集合），获取需要的那部分 JSON value 并处理。

# 测试三方库

| **库名**                                                                | **Star** | **encoder** | **decoder** | **compatible with** **encoding/json** |
| ----------------------------------------------------------------------- | -------- | ----------- | ----------- | ------------------------------------- |
| StdLib：[encoding/json](https://pkg.go.dev/encoding/json)               | -        | ✔️          | ✔️          | N/A                                   |
| FastJson：[valyala/fastjson](https://github.com/valyala/fastjson)       | 1.8k     | ✔️          | ✔️          | ❌                                    |
| GJson：[tidwall/gjson](https://github.com/tidwall/gjson)                | 11.8k    | ✔️          | ✔️          | ❌                                    |
| JsonParser：[buger/jsonparser](https://github.com/buger/jsonparser)     | 5k       | ✔️          | ✔️          | ❌                                    |
| JsonIter：[json-iterator/go](https://github.com/json-iterator/go)       | 11.9k    | ✔️          | ✔️          | 部分兼容                              |
| GoJson：[goccy/go-json](https://github.com/goccy/go-json)               | 2.1k     | ✔️          | ✔️          | ✔️                                    |
| EasyJson：[mailru/easyjson](https://github.com/mailru/easyjson)         | 4.1k     | ✔️          | ✔️          | ❌                                    |
| Sonic：[bytedance/sonic](https://github.com/bytedance/sonic)            | 4.1k     | ✔️          | ✔️          | ✔️                                    |
| Sonnet：[sugawarayuuta/sonnet](https://github.com/sugawarayuuta/sonnet) | 20       | ❌          | ✔️          | 部分兼容                              |

## 功能对比

| **相关库** | unmarshal (interface) | unmarshal (struct) | get&set | stream | 备注                                                                                                                                                                                                                                                                        |
| ---------- | --------------------- | ------------------ | ------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| StdLib     | ✔️                    | ✔️                 | ❌      | ✔️     |                                                                                                                                                                                                                                                                             |
| FastJson   | ❌                    | ❌                 | ✔️      | ❌     | 通过遍历 JSON 字符串的字节来挨个解析,返回其值 []byte，由业务方自行处理，牺牲了一定的兼容性，但功能上各有特色。fastjson 的 api 操作最简单；gjson 提供了模糊查找的功能，自定义程度最高；jsonparser 在实现高性能的解析过程中，还可以插入回调函数执行，提供了一定程度上的便利； |
| Gjson      | ✔️                    | ❌                 | ✔️      | ❌     |                                                                                                                                                                                                                                                                             |
| JsonParser | ❌                    | ❌                 | ✔️      | ❌     |                                                                                                                                                                                                                                                                             |
| EasyJson   | -                     | ✔️                 | -       | -      | 不使用反射通过代码生成的方式，类似 protobuf 为每一个结构体生成序列化的代码，具有强入侵性                                                                                                                                                                                    |
| JsonIter   | ✔️                    | ❌                 | ✔️      | ✔️     | 尽量减少反射的使用，eg：同一类型的对象，只调用 reflect 解析一次之后即缓存下来。尽量减少不必要的内存分配与复制                                                                                                                                                               |
| GoJson     | ✔️                    | ✔️                 | ❌      | ✔️     |                                                                                                                                                                                                                                                                             |
| Sonic      | ✔️                    | ✔️                 | ✔️      | ✔️     |                                                                                                                                                                                                                                                                             |
| Sonnet     | ✔️                    | ✔️                 | ❌      | ❌     |                                                                                                                                                                                                                                                                             |

**为什么不推荐当前使用最广泛的第三方库 jsoniter？**

Go 1.8 之前，官方 json 库的性能就收到多方诟病。不过随着 go 版本的迭代，标准 json 库的性能也越来越高，jsonter 的性能优势也越来越窄。如果希望有极致的性能，应该选择 easyjson 等方案而不是 jsoniter，而且 jsoniter 近年已经不活跃了。

## 性能对比

涉及的测试数据&测试方法，详情参见：https://github.com/zhao520a1a/go-base/blob/master/json/benchmark_test/bench.sh

| **库名** | **version**                        |
| -------- | ---------------------------------- |
| StdLib   | v1.19                              |
| Sjson    | v1.2.5                             |
| GJson    | v1.14.4                            |
| JsonIter | v1.1.13                            |
| GoJson   | v0.10.1                            |
| Sonic    | v1.8.3                             |
| Sonnet   | v0.0.0-20230211095525-cfcf1c3a9fc4 |

根据样本 JSON 的 key 数量和深度分为三个量级：

- [Small](https://github.com/zhao520a1a/go-base/blob/master/json/testdata/small.go) (400B, 11 keys, 3 layers)

- [Medium](https://github.com/zhao520a1a/go-base/blob/master/json/testdata/medium.go) (13KB, 300+ key, 6 layers)
- [Large](https://github.com/zhao520a1a/go-base/blob/master/json/testdata/large.json) (635KB, 10000+ key, 6 layers)

### 解析小 JSON 字符串

```json
BenchmarkDecoder_Generic_StdLib-12                       1000000              6986 ns/op          52.25 MB/s        3474 B/op         91 allocs/op
BenchmarkDecoder_Generic_JsonIter-12                     1000000              7366 ns/op          49.55 MB/s        3748 B/op        112 allocs/op
BenchmarkDecoder_Generic_GoJson-12                       1000000              6961 ns/op          52.43 MB/s        4279 B/op        105 allocs/op
BenchmarkDecoder_Generic_Sonic-12                        1000000              4093 ns/op          89.17 MB/s        4567 B/op         42 allocs/op
BenchmarkDecoder_Generic_Sonic_V1-12                     1000000              4474 ns/op          81.58 MB/s        4363 B/op         71 allocs/op
BenchmarkDecoder_Generic_Sonic_Fast-12                   1000000              3927 ns/op          92.95 MB/s        4171 B/op         41 allocs/op
BenchmarkDecoder_Generic_Sonnet-12                       1000000              4743 ns/op          76.95 MB/s        3330 B/op         80 allocs/op
BenchmarkDecoder_Parallel_Generic_StdLib-12              1000000              2387 ns/op         152.89 MB/s        3474 B/op         91 allocs/op
BenchmarkDecoder_Parallel_Generic_JsonIter-12            1000000              2411 ns/op         151.37 MB/s        3749 B/op        112 allocs/op
BenchmarkDecoder_Parallel_Generic_GoJson-12              1000000              2680 ns/op         136.20 MB/s        4283 B/op        105 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic-12               1000000              1641 ns/op         222.45 MB/s        4615 B/op         42 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic_V1-12            1000000              1707 ns/op         213.82 MB/s        4383 B/op         71 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic_Fast-12          1000000              1688 ns/op         216.22 MB/s        4190 B/op         41 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonnet-12              1000000              2154 ns/op         169.45 MB/s        3331 B/op         80 allocs/op
BenchmarkDecoder_Binding_StdLib-12                       1000000              7369 ns/op          49.53 MB/s        1056 B/op         36 allocs/op
BenchmarkDecoder_Binding_JsonIter-12                     1000000              2281 ns/op         160.01 MB/s         688 B/op         31 allocs/op
BenchmarkDecoder_Binding_GoJson-12                       1000000              1786 ns/op         204.36 MB/s         939 B/op         19 allocs/op
BenchmarkDecoder_Binding_Sonic-12                        1000000              1697 ns/op         215.14 MB/s        1797 B/op          8 allocs/op
BenchmarkDecoder_Binding_Sonic_V1-12                     1000000              1720 ns/op         212.23 MB/s        1464 B/op         14 allocs/op
BenchmarkDecoder_Binding_Sonic_Fast-12                   1000000              1616 ns/op         225.85 MB/s        1403 B/op          7 allocs/op
BenchmarkDecoder_Binding_Sonnet-12                       1000000              4747 ns/op          76.89 MB/s        3330 B/op         80 allocs/op
BenchmarkDecoder_Parallel_Binding_StdLib-12              1000000              1835 ns/op         198.92 MB/s        1055 B/op         36 allocs/op
BenchmarkDecoder_Parallel_Binding_JsonIter-12            1000000               638.5 ns/op       571.62 MB/s         688 B/op         31 allocs/op
BenchmarkDecoder_Parallel_Binding_GoJson-12              1000000               640.7 ns/op       569.68 MB/s         942 B/op         19 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic-12               1000000               557.6 ns/op       654.64 MB/s        1868 B/op          8 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic_V1-12            1000000               523.6 ns/op       697.05 MB/s        1496 B/op         14 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic_Fast-12          1000000               504.4 ns/op       723.67 MB/s        1436 B/op          7 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonnet-12              1000000               718.4 ns/op       508.06 MB/s         751 B/op         17 allocs/op
BenchmarkEncoder_Generic_StdLib-12                       1000000             10142 ns/op          35.99 MB/s        3273 B/op         67 allocs/op
BenchmarkEncoder_Generic_JsonIter-12                     1000000              5373 ns/op          67.93 MB/s        1024 B/op         16 allocs/op
BenchmarkEncoder_Generic_GoJson-12                       1000000              4903 ns/op          74.44 MB/s         961 B/op          2 allocs/op
BenchmarkEncoder_Generic_Sonic-12                        1000000              2405 ns/op         151.76 MB/s         479 B/op          4 allocs/op
BenchmarkEncoder_Generic_Sonic_V1-12                     1000000              2734 ns/op         133.49 MB/s         732 B/op          4 allocs/op
BenchmarkEncoder_Generic_Sonic_Fast-12                   1000000              2329 ns/op         156.72 MB/s         469 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic-12               1000000               475.6 ns/op       767.50 MB/s         487 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Generic_JsonIter-12            1000000              1248 ns/op         292.50 MB/s        1024 B/op         16 allocs/op
BenchmarkEncoder_Parallel_Generic_GoJson-12              1000000              1636 ns/op         223.16 MB/s         961 B/op          2 allocs/op
BenchmarkEncoder_Parallel_Generic_StdLib-12              1000000              3971 ns/op          91.92 MB/s        3273 B/op         67 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic_V1-12            1000000              1003 ns/op         363.81 MB/s         760 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic_Fast-12          1000000               537.9 ns/op       678.51 MB/s         492 B/op          4 allocs/op
BenchmarkEncoder_Binding_StdLib-12                       1000000              2073 ns/op         176.07 MB/s         384 B/op          1 allocs/op
BenchmarkEncoder_Binding_JsonIter-12                     1000000              2209 ns/op         165.26 MB/s         392 B/op          2 allocs/op
BenchmarkEncoder_Binding_GoJson-12                       1000000              1172 ns/op         311.31 MB/s         384 B/op          1 allocs/op
BenchmarkEncoder_Binding_Sonic-12                        1000000               842.2 ns/op       433.41 MB/s         492 B/op          4 allocs/op
BenchmarkEncoder_Binding_Sonic_V1-12                     1000000               956.8 ns/op       381.50 MB/s         757 B/op          4 allocs/op
BenchmarkEncoder_Binding_Sonic_Fast-12                   1000000               814.0 ns/op       448.41 MB/s         490 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_StdLib-12              1000000               452.7 ns/op       806.23 MB/s         384 B/op          1 allocs/op
BenchmarkEncoder_Parallel_Binding_JsonIter-12            1000000               508.1 ns/op       718.34 MB/s         392 B/op          2 allocs/op
BenchmarkEncoder_Parallel_Binding_GoJson-12              1000000               331.9 ns/op      1099.89 MB/s         384 B/op          1 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic-12               1000000               184.7 ns/op      1976.14 MB/s         488 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic_V1-12            1000000               238.7 ns/op      1529.08 MB/s         745 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic_Fast-12          1000000               185.8 ns/op      1964.13 MB/s         496 B/op          4 allocs/op
```

### 解析中 JSON 字符串

```json
BenchmarkDecoder_Generic_StdLib-12                        100000            134048 ns/op          97.26 MB/s       50870 B/op        772 allocs/op
BenchmarkDecoder_Generic_JsonIter-12                      100000             94131 ns/op         138.50 MB/s       55779 B/op       1068 allocs/op
BenchmarkDecoder_Generic_GoJson-12                        100000             91549 ns/op         142.40 MB/s       66358 B/op        973 allocs/op
BenchmarkDecoder_Generic_Sonic-12                         100000             57213 ns/op         227.87 MB/s       62757 B/op        314 allocs/op
BenchmarkDecoder_Generic_Sonic_V1-12                      100000             67120 ns/op         194.23 MB/s       56800 B/op        723 allocs/op
BenchmarkDecoder_Generic_Sonic_Fast-12                    100000             54601 ns/op         238.77 MB/s       49020 B/op        313 allocs/op
BenchmarkDecoder_Generic_Sonnet-12                        100000             67423 ns/op         193.36 MB/s       50222 B/op        739 allocs/op
BenchmarkDecoder_Parallel_Generic_StdLib-12               100000             50068 ns/op         260.38 MB/s       50875 B/op        772 allocs/op
BenchmarkDecoder_Parallel_Generic_JsonIter-12             100000             38097 ns/op         342.20 MB/s       55790 B/op       1068 allocs/op
BenchmarkDecoder_Parallel_Generic_GoJson-12               100000             33294 ns/op         391.57 MB/s       66364 B/op        974 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic-12                100000             21363 ns/op         610.25 MB/s       63889 B/op        314 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic_V1-12             100000             24666 ns/op         528.55 MB/s       56823 B/op        723 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic_Fast-12           100000             19639 ns/op         663.84 MB/s       49063 B/op        313 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonnet-12               100000             33211 ns/op         392.55 MB/s       50233 B/op        739 allocs/op
BenchmarkDecoder_Binding_StdLib-12                        100000            119862 ns/op         108.77 MB/s       10576 B/op        208 allocs/op
BenchmarkDecoder_Binding_JsonIter-12                      100000             37648 ns/op         346.29 MB/s       14672 B/op        385 allocs/op
BenchmarkDecoder_Binding_GoJson-12                        100000             30700 ns/op         424.66 MB/s       22031 B/op         49 allocs/op
BenchmarkDecoder_Binding_Sonic-12                         100000             31562 ns/op         413.05 MB/s       38060 B/op         35 allocs/op
BenchmarkDecoder_Binding_Sonic_V1-12                      100000             32212 ns/op         404.72 MB/s       27327 B/op        137 allocs/op
BenchmarkDecoder_Binding_Sonic_Fast-12                    100000             28587 ns/op         456.05 MB/s       24280 B/op         34 allocs/op
BenchmarkDecoder_Binding_Sonnet-12                        100000             68974 ns/op         189.01 MB/s       50228 B/op        739 allocs/op
BenchmarkDecoder_Parallel_Binding_StdLib-12               100000             27176 ns/op         479.73 MB/s       10575 B/op        208 allocs/op
BenchmarkDecoder_Parallel_Binding_JsonIter-12             100000             11446 ns/op        1138.96 MB/s       14674 B/op        385 allocs/op
BenchmarkDecoder_Parallel_Binding_GoJson-12               100000              9237 ns/op        1411.39 MB/s       22102 B/op         49 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic-12                100000              9081 ns/op        1435.69 MB/s       39066 B/op         35 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic_V1-12             100000              9358 ns/op        1393.20 MB/s       27372 B/op        137 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic_Fast-12           100000              8292 ns/op        1572.23 MB/s       24347 B/op         34 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonnet-12               100000             11304 ns/op        1153.32 MB/s       11656 B/op        130 allocs/op
BenchmarkEncoder_Generic_StdLib-12                        100000            110818 ns/op         117.64 MB/s       44266 B/op        751 allocs/op
BenchmarkEncoder_Generic_JsonIter-12                      100000             44940 ns/op         290.10 MB/s       14347 B/op        115 allocs/op
BenchmarkEncoder_Generic_GoJson-12                        100000             68311 ns/op         190.85 MB/s       23464 B/op         18 allocs/op
BenchmarkEncoder_Generic_Sonic-12                         100000             33923 ns/op         384.31 MB/s       13759 B/op          4 allocs/op
BenchmarkEncoder_Generic_Sonic_Fast-12                    100000             23436 ns/op         556.28 MB/s        9727 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Generic_StdLib-12               100000             40058 ns/op         325.45 MB/s       44288 B/op        751 allocs/op
BenchmarkEncoder_Parallel_Generic_JsonIter-12             100000             11915 ns/op        1094.20 MB/s       14358 B/op        115 allocs/op
BenchmarkEncoder_Parallel_Generic_GoJson-12               100000             20948 ns/op         622.36 MB/s       23445 B/op         18 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic-12                100000             10335 ns/op        1261.48 MB/s       14056 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic_Fast-12           100000              5895 ns/op        2211.64 MB/s        9821 B/op          4 allocs/op
BenchmarkEncoder_Binding_StdLib-12                        100000             18100 ns/op         720.29 MB/s        9480 B/op          1 allocs/op
BenchmarkEncoder_Binding_JsonIter-12                      100000             22245 ns/op         586.08 MB/s        9487 B/op          2 allocs/op
BenchmarkEncoder_Binding_GoJson-12                        100000              7886 ns/op        1653.13 MB/s        9482 B/op          1 allocs/op
BenchmarkEncoder_Binding_Sonic-12                         100000              5659 ns/op        2303.64 MB/s       14253 B/op          4 allocs/op
BenchmarkEncoder_Binding_Sonic_Fast-12                    100000              4961 ns/op        2627.89 MB/s       10056 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_StdLib-12               100000              4468 ns/op        2917.64 MB/s        9487 B/op          1 allocs/op
BenchmarkEncoder_Parallel_Binding_JsonIter-12             100000              5370 ns/op        2427.56 MB/s        9496 B/op          2 allocs/op
BenchmarkEncoder_Parallel_Binding_GoJson-12               100000              2928 ns/op        4453.05 MB/s        9500 B/op          1 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic-12                100000              1348 ns/op        9670.27 MB/s       14279 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic_Fast-12           100000              1162 ns/op        11219.60 MB/s      10056 B/op          4 allocs/op
```

### 解析大 JSON 字符串

```go
BenchmarkDecoder_Generic_StdLib-12                          5000           6120476 ns/op         103.18 MB/s     2151910 B/op      31261 allocs/op
BenchmarkDecoder_Generic_JsonIter-12                        5000           4260781 ns/op         148.22 MB/s     2427840 B/op      45043 allocs/op
BenchmarkDecoder_Generic_GoJson-12                          5000           4088162 ns/op         154.47 MB/s     2757799 B/op      39700 allocs/op
BenchmarkDecoder_Generic_Sonic-12                           5000           2561050 ns/op         246.58 MB/s     2609818 B/op      12137 allocs/op
BenchmarkDecoder_Generic_Sonic_V1-12                        5000           3041447 ns/op         207.64 MB/s     2344109 B/op      29781 allocs/op
BenchmarkDecoder_Generic_Sonic_Fast-12                      5000           2488119 ns/op         253.81 MB/s     1967848 B/op      12136 allocs/op
BenchmarkDecoder_Generic_Sonnet-12                          5000           3212028 ns/op         196.61 MB/s     2096696 B/op      30183 allocs/op
BenchmarkDecoder_Parallel_Generic_StdLib-12                 5000           1534652 ns/op         411.50 MB/s     2152041 B/op      31262 allocs/op
BenchmarkDecoder_Parallel_Generic_JsonIter-12               5000           1197112 ns/op         527.53 MB/s     2427316 B/op      45043 allocs/op
BenchmarkDecoder_Parallel_Generic_GoJson-12                 5000           1046451 ns/op         603.48 MB/s     2756561 B/op      39698 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic-12                  5000            699298 ns/op         903.07 MB/s     2614464 B/op      12136 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic_V1-12               5000            906161 ns/op         696.91 MB/s     2343733 B/op      29780 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonic_Fast-12             5000            784229 ns/op         805.27 MB/s     1967387 B/op      12135 allocs/op
BenchmarkDecoder_Parallel_Generic_Sonnet-12                 5000           1057777 ns/op         597.02 MB/s     2096632 B/op      30182 allocs/op
BenchmarkDecoder_Binding_StdLib-12                          5000           5519137 ns/op         114.42 MB/s      601858 B/op       5848 allocs/op
BenchmarkDecoder_Binding_JsonIter-12                        5000           1831864 ns/op         344.74 MB/s      748192 B/op      18781 allocs/op
BenchmarkDecoder_Binding_GoJson-12                          5000           1178029 ns/op         536.08 MB/s      901550 B/op       2799 allocs/op
BenchmarkDecoder_Binding_Sonic-12                           5000           1199569 ns/op         526.45 MB/s     1105079 B/op       1683 allocs/op
BenchmarkDecoder_Binding_Sonic_V1-12                        5000           1232027 ns/op         512.58 MB/s      560149 B/op       4533 allocs/op
BenchmarkDecoder_Binding_Sonic_Fast-12                      5000           1125198 ns/op         561.25 MB/s      464553 B/op       1682 allocs/op
BenchmarkDecoder_Binding_Sonnet-12                          5000           3055920 ns/op         206.65 MB/s     2096695 B/op      30183 allocs/op
BenchmarkDecoder_Parallel_Binding_StdLib-12                 5000           1182782 ns/op         533.92 MB/s      601871 B/op       5848 allocs/op
BenchmarkDecoder_Parallel_Binding_JsonIter-12               5000            476816 ns/op        1324.44 MB/s      748068 B/op      18781 allocs/op
BenchmarkDecoder_Parallel_Binding_GoJson-12                 5000            271643 ns/op        2324.79 MB/s      901943 B/op       2795 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic-12                  5000            281690 ns/op        2241.87 MB/s     1108846 B/op       1683 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic_V1-12               5000            296465 ns/op        2130.15 MB/s      560588 B/op       4533 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonic_Fast-12             5000            264516 ns/op        2387.44 MB/s      465060 B/op       1682 allocs/op
BenchmarkDecoder_Parallel_Binding_Sonnet-12                 5000            359303 ns/op        1757.61 MB/s      396600 B/op       4348 allocs/op
BenchmarkEncoder_Generic_StdLib-12                          5000           5943144 ns/op         106.26 MB/s     1920483 B/op      31055 allocs/op
BenchmarkEncoder_Generic_JsonIter-12                        5000           2492510 ns/op         253.36 MB/s      637167 B/op       3793 allocs/op
BenchmarkEncoder_Generic_GoJson-12                          5000           3550643 ns/op         177.86 MB/s     1100084 B/op        544 allocs/op
BenchmarkEncoder_Generic_Sonic-12                           5000           1134123 ns/op         556.83 MB/s      470115 B/op          5 allocs/op
BenchmarkEncoder_Generic_Sonic_V1-12                        5000           1649071 ns/op         382.95 MB/s      709381 B/op          5 allocs/op
BenchmarkEncoder_Generic_Sonic_Fast-12                      5000           1147522 ns/op         550.33 MB/s      470639 B/op          5 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic-12                  5000            240012 ns/op        2631.17 MB/s      472896 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Generic_JsonIter-12               5000            485174 ns/op        1301.62 MB/s      644095 B/op       3793 allocs/op
BenchmarkEncoder_Parallel_Generic_GoJson-12                 5000            749546 ns/op         842.53 MB/s     1060605 B/op        550 allocs/op
BenchmarkEncoder_Parallel_Generic_StdLib-12                 5000           1702450 ns/op         370.94 MB/s     1922308 B/op      31055 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic_V1-12               5000            582658 ns/op        1083.85 MB/s      712830 B/op          5 allocs/op
BenchmarkEncoder_Parallel_Generic_Sonic_Fast-12             5000            348096 ns/op        1814.19 MB/s      471770 B/op          4 allocs/op
BenchmarkEncoder_Binding_StdLib-12                          5000           1115137 ns/op         566.31 MB/s      324698 B/op       1423 allocs/op
BenchmarkEncoder_Binding_JsonIter-12                        5000           1087129 ns/op         580.90 MB/s      275567 B/op        314 allocs/op
BenchmarkEncoder_Binding_GoJson-12                          5000            537630 ns/op        1174.63 MB/s      265792 B/op         15 allocs/op
BenchmarkEncoder_Binding_Sonic-12                           5000            212572 ns/op        2970.83 MB/s      264782 B/op          4 allocs/op
BenchmarkEncoder_Binding_Sonic_V1-12                        5000            255639 ns/op        2470.34 MB/s      391700 B/op          4 allocs/op
BenchmarkEncoder_Binding_Sonic_Fast-12                      5000            216416 ns/op        2918.05 MB/s      265716 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_StdLib-12                 5000            186556 ns/op        3385.12 MB/s      325774 B/op       1423 allocs/op
BenchmarkEncoder_Parallel_Binding_JsonIter-12               5000            174684 ns/op        3615.17 MB/s      278099 B/op        314 allocs/op
BenchmarkEncoder_Parallel_Binding_GoJson-12                 5000            115085 ns/op        5487.37 MB/s      268657 B/op         15 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic-12                  5000             43834 ns/op        14406.79 MB/s     267855 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic_V1-12               5000             63657 ns/op        9920.59 MB/s      394323 B/op          4 allocs/op
BenchmarkEncoder_Parallel_Binding_Sonic_Fast-12             5000             45873 ns/op        13766.56 MB/s     267750 B/op          4 allocs/op
```

| **库名** | **数据量**   | **泛型编码\*\***性能\*\* | **定型编码性能** | **泛型解码** | **定型解码** |
| -------- | ------------ | ------------------------ | ---------------- | ------------ | ------------ |
| StdLib   | 小           | ⭐️                      | ⭐️              | ⭐️⭐️       | ⭐️          |
| 中       | ⭐️          | ⭐️                      | ⭐️              | ⭐️          |              |
| 大       | ⭐️          | ⭐️                      | ⭐️              | ⭐️          |              |
| JsonIter | 小           | ⭐️⭐️⭐️                | ⭐️              | ⭐️⭐️       | ⭐️⭐️⭐️    |
| 中       | ⭐️⭐️⭐️    | ⭐️                      | ⭐️⭐️           | ⭐️⭐️       |              |
| 大       | ⭐️⭐️⭐️⭐  | ⭐️                      | ⭐️⭐️           | ⭐️⭐️       |              |
| GoJson   | 小           | ⭐️⭐️⭐️                | ⭐️⭐️           | ⭐️          | ⭐️⭐️⭐️    |
| 中       | ⭐️⭐️       | ⭐️⭐️⭐️                | ⭐️⭐️⭐️        | ⭐️⭐️⭐️⭐️ |              |
| 大       | ⭐️⭐️⭐️    | ⭐️⭐️⭐️                | ⭐️⭐️⭐️        | ⭐️⭐️⭐️⭐️ |              |
| Sonic    | 小           | ⭐️⭐️⭐️⭐              | ⭐️⭐️⭐️⭐️     | ⭐️⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️ |
| 中       | ⭐️⭐️⭐️⭐️ | ⭐️⭐️⭐️⭐️             | ⭐️⭐️⭐️⭐️     | ⭐️⭐️⭐️⭐️ |              |
| 大       | ⭐️⭐️⭐️⭐  | ⭐️⭐️⭐️⭐              | ⭐️⭐️⭐️⭐️     | ⭐️⭐️⭐️⭐️ |              |
| Sonnet   | 小           | -                        | -                | ⭐️⭐️⭐️    | ⭐️⭐️       |
| 中       | -            | -                        | ⭐️⭐️⭐️        | ⭐️⭐️       |              |
| 大       | -            | -                        | ⭐️⭐️⭐️        | ⭐️⭐️       |              |

# 优化思路

## 定型编解码优化

核心思想：**将模型解释与数据处理逻辑分离，让前者在提前固定下来，进而消除反射，提升性能。**

对于有 schema 的定型编解码场景而言，很多运算其实不需要在“运行时”执行。

eg：如果业务模型中确定了某个 JSON key 的值一定是布尔类型，那么我们就可以在序列化阶段直接输出这个对象对应的 JSON 值（‘true’或‘false’），并不需要再检查这个对象的具体类型。

### 优化数据处理逻辑

JsonIter 使用函数组装模式，具体方法：将结构解释为逐个字段的编码和解码函数，然后将其组装并缓存为整个对象对应的编解码器，运行时再加载出来处理 JSON，将反射的性能损失成本降到最低。

但这是否能一劳永逸呢？不是。因为原因是这个实现转化为大量的接口封装和函数调用栈。在实际测试中，发现随着 JSON 数据量级的增长，function-call 开销也成倍放大。

```go
type cache struct {
	functions map[*rtype]function
	lock      sync.Mutex
}

var (
	global = func() [caches]*cache {
		var caches [caches]*cache
		for idx := range caches {
			caches[idx] = &cache{functions: make(map[*rtype]function, 4)}
		}
		return caches
	}()
)
```

调用接口涉及动态寻址，汇编函数不能被内联，而 Golang 的函数调用性能很差（没有逐个寄存器的参数传递）。

**有什么办法可以避免动态汇编的函数调用开销吗？**

业界实现方式目前主要有两种：代码生成 code-gen 和 即时编译 JIT。

### code-gen

采用 code-gen(代码生成)，代表性的库有：easyjson；

库开发者实现起来相对简单，性能高，但是它伴随着模式依赖性和便利性的损失，增加业务代码的维护成本和局限性，无法做到秒级热更新（这也是代码生成方式的 JSON 库受众并不广泛的原因）

### JIT

JIT (即时编译)的核心思想是将模型解释与数据处理逻辑分离，让前者在“编译期”固定下来。**将编译过程移到了程序的加载（或首次解析）阶段**，只需要提供 JSON schema 对应的结构体类型信息，就可以一次性编译生成对应的编解码器(以 Golang 函数的形式缓存到堆外内存)并高效执行。

案例：https://github.com/sugawarayuuta/sonnet

```go
type cache struct {
	functions map[*rtype]function
	lock      sync.Mutex
}

var (
	global = func() [caches]*cache {
		var caches [caches]*cache
		for idx := range caches {
			caches[idx] = &cache{functions: make(map[*rtype]function, 4)}
		}
		return caches
	}()
)

func load(typ *rtype) (function, bool) {
	do, ok := global[uintptr(unsafe.Pointer(typ))%caches].functions[typ]
	return do, ok
}

func save(typ *rtype, do function) {
	cache := global[uintptr(unsafe.Pointer(typ))%caches]
	cache.lock.Lock()
	cache.functions[typ] = do
	cache.lock.Unlock()
}
```

## 泛型编解码优化

### 性能差只是因为没有 schema 吗？

可以对比一下 C++ 的 JSON 库，如 rappidjson、simdjson，它们的解析方式都是泛型的，但性能仍然很好；

标准库泛型解析性能差的根本原因在于它采用了 **Go 标准泛型——interface（map[string]interface{}）作为 JSON 的编解码对象**。这其实是一种糟糕的选择：首先是数据反序列化的过程中，map 插入的开销很高；其次在数据序列化过程中，map 遍历也远不如数组高效。

优化思路：如果用一种与 JSON AST 更贴近的数据结构来描述，不但可以让转换过程更加简单，甚至可以实现按需加载（lazy-load）。

### lazy-load

GJson 在单键查找的场景下有很大的优势。这是因为它的查找是通过按需加载实现的，它巧妙地跳过了传递值，有效地减少了很多不必要的解析，但其实跳过也是一种轻量级解析（处理 JSON 控制字符“[”、“{”等）。但当涉及到多键查找时，Gjson 做的事比 StdLib 更糟糕，这是其跳过机制的副作用(相同路径查找导致的重复开销)。

## buffer-reuse

复用 encode buffer，通过使用 sync.Pool 重用用于先前编码的缓冲区，减少 encode buffer 的内存分配次数。

```go
type buffer struct {
    data []byte
}

var bufPool = sync.Pool{
    New: func() interface{} {
        return &buffer{data: make([]byte, 0, 1024)}
    },
}

buf := bufPool.Get().(*buffer)
data := encode(buf.data) // reuse buf.data

newBuf := make([]byte, len(data))
copy(newBuf, buf)

buf.data = data
bufPool.Put(buf)
```

# Sonic

## Sonic 为什么性能高？

主要通过基于汇编进行开发，充分利用向量化（SIMD）指令、优化内存布局和按需解析等关键技术，大幅提高了序列化反序列化性能。

![img](Go%20JSON%20%E5%BA%93%E8%B0%83%E7%A0%94/1679235214712-4c7ab60e-dd98-4584-b6a7-4eb98b153639-9412240.png)

- 借鉴 json-iterator 的组装各类型处理函数的实现，不同之处在于直接编译出来，减少了函数调用的开销。
- simd-json 虽然也使用了 simd，但是使用的是 go 的编译器，相比 clang 所做的优化更少。
- 使用 cgo(可以直接用 golang 编译并调用 C 代码)的实现虽然更加简便，对代码进行了深度优化， 但 cgo 在调用 c 代码的时候引入了调度、切换线程栈等开销，会造成较大（有的场景中高达 20 多倍）的性能损耗。

### 离线编译

对于 go 语言编译优化的不足，核心计算函数(热点操作)使用 C 语言编写，使用 Clang 的深度优化编译选项，并开发了一套 asm2asm 工具，将完全优化的 x86 汇编翻译成 plan9 汇编，加载到 Golang 运行时，以供调用。

#### SIMD

JSON 文本的处理与计算。其中一些问题在业界已经有比较成熟高效的解决方案，如浮点数转字符串算法 Ryu，整数转字符串的查表法等；而一些问题逻辑相对简单，但是可能会面对较大数量级的文本，如 JSON string 的 unquote\quote 处理、空白字符的跳过等，也需要某种技术手段来提升处理能力，而 SIMD 就是一种用于并行处理大规模数据的技术，

SIMD（Single-Instruction-Multi-Data 单指令流多数据流）它是一种采用一个控制器来控制多个处理器，同时对一组数据中的每一个数据分别执行相同的操作，从而实现空间上的并行性技术。例如：X86 的 SSE 或者 AVX2 指令集，以及 ARM 的 NEON 指令集等。它作为一组特殊的 CPU 指令，用于矢量数据的并行处理。目前，它被大多数 CPU 所支持，并广泛用于图像处理和大数据计算中。

SIMD 在 JSON 处理中也很有用，[simdjson-go](https://github.com/minio/simdjson-go) 在大型 JSON 场景（>100KB）中非常有竞争力。然而，对于一些极小的或不规则的字符串，SIMD 所需的额外负载操作将导致性能下降。因此， 对于大数据和小数据并存的实际场景，采用预设条件判断（字符串大小、浮动精度等），将 SIMD 和标量指令结合起来，以达到最佳适应性。

#### 汇编转换-asm2asm

一些关键的计算函数是否可以用另一种执行效率更高的语言来编写呢？C/Clang 是一个理想的编译工具，但关键是如何将优化后的汇编嵌入 Golang 中？

由于 clang 编译出来的是 x86 汇编，而 golang 编译出来的是 plan9 汇编。为了在 golang 中调用 clang 编译出来的汇编，字节开发了一个工具(tools/asm2asm)将 x86 的汇编转换为 plan9。

### JIT 汇编

针对编解码器动态装配的函数调用开销，采用 JIT 技术在运行时对模式对应的操作码（asm）进行装配，最后以 Golang 函数的形式缓存到堆外内存。因为编译后的编解码函数是一个集成函数，可以大大减少函数调用，同时保证灵活性；

#### RCU cache

为了提升 codec cache 的加载速度，每个结构体对应的序列化/反序列化字节码可以缓存起来，后面直接调用，以减少运行时汇编操作的执行次数（缓存足够大的时候只需要执行一次）。Sync.Map 最初是用来缓存编解码器的，但对于准静态（读远多于写）、较少元素（通常不超过几十个）的场景来说，其性能并不理想，所以用“开放寻址哈希+RCU 技术”重新实现了一个高性能和并发安全的缓存。

#### 已知结构体的场景

JIT 汇编是比较耗时的，在线进行会导致首次请求耗时较高。对于 json 对应的结构体已知的服务场景，可以在预先生成好汇编后的字节码，不用引入 JIT 机制。

#### 其他优化

- 无栈内存管理：自己维护变量栈（内存池），避免 Go 函数栈扩展。
- 自动生成跳转表，加速 generic decoding 的分支跳转。
- 使用寄存器传参：将使用频繁的变量放到固定的寄存器上（如 JSON buffer、结构体指针），尽量避免 memory load & store。
- 重写函数调用：由于汇编函数不能内联到 go 函数中，函数调用引入的开销甚至会抵消 SIMD 带来的性能提升，因此在 JIT 中重新实现了一组轻量级的函数调用（维护全局函数表+函数 offset）。

### lazy-load

针对泛型编解码，基于 map 开销较大的考虑，sonic 实现了更能符合 json 结构的树形 AST；针对部分解析，使用 lazy-load 技术并且以一种更自适应和有效的方式处理多字段查询的场景。

考虑到解析和跳过之间的巨大速度差距，用 node {type, length, pointer} 表示任意一个 JSON 数据节点，并结合树与数组结构描述节点之间的层级关系。将 lazy-load 机制到 AST 解析器中，以一种更加自适应和高效的方式来减少多键查询的开销。

```go
type Node struct {
    v int64
    t types.ValueType
    p unsafe.Pointer
}
```

![img](Go%20JSON%20%E5%BA%93%E8%B0%83%E7%A0%94/1678849837151-7839eba4-c94b-4bbe-bea2-7eabd7b0413d-9412226.png)

sonic-ast 实现了一种有状态、可伸缩的 JSON 解析过程：当使用者 get 某个 key 时，sonic 采用 skip 计算来轻量化跳过要获取的 key 之前的 json 文本；对于该 key 之后的 JSON 节点，直接不做任何的解析处理；仅使用者真正需要的 key 才完全解析。

**如何解决\*\***相同路径查找导致的重复开销？\*\*

sonic 在对于子节点 skip 处理过程增加了一个步骤，将跳过 JSON 的 key、起始位、结束位记录下来，分配一个 Raw-JSON 类型的节点保存下来，这样二次 skip 就可以直接基于节点的 offset 进行。同时 sonic-ast 支持了节点的更新、插入和序列化，甚至支持将任意 Go types 转为节点并保存下来

总而言之，sonic-ast 可以作为一种通用的泛型数据容器替代 Go interface。

### Sonic 落地

golang 现有的库中没有一个可以在全场景下保持优异的性能，即使是 json-iterator，在泛型编解码、大数据量级场景下的性能也会下降。与其他语言相比，golang 的各种 json 库速度都慢了很多，存在优化空间。

## 适用场景

由于 sonic 优化的是 json 操作，所以在 json 操作的 cpu 开销占比较大的服务场景中收益会比较明显。比如网关、转发和入口服务等。

## 快速试用 sonic

想要了解 sonic 会对自己的服务产生多大的性能提升，评估是否值得切换，可以下面的方式较小侵入地将当前使用的 json 库切换为 sonic：使用[http://github.com/brahma-adshonor/gohook](https://link.zhihu.com/?target=http%3A//github.com/brahma-adshonor/gohook)，在 main 函数的入口处 hook 当前使用的 json 库函数为 sonic 中对等的函数。

```go
import "github.com/brahma-adshonor/gohook"

func main() {
    // 在main函数的入口hook当前使用的json库（如encoding/json）
    gohook.Hook(json.Marshal, sonic.Marshal, nil)
    gohook.Hook(json.Unmarshal, sonic.Unmarshal, nil)
}
```

hook 是函数级的，因此可以具体验证具体函数的性能提升，也可以部分函数使用 sonic（出于对某些函数的不信任、或者自己有性能更优异或更稳定的实现）。

注意：[gohook](http://github.com/brahma-adshonor/gohook)的大概实现是向被 hook 的函数地址中写入跳转指令，直接跳转到新的函数地址。 _需要注意的是，gohook 未经过生产环境验证，建议仅测试使用。_

## 使用注意事项

### key 排序

sonic 在序列化时默认是不对 key 进行排序的。json 的规范也与顺序无关，但若需要 json 是有序的，可以在序列化时选择排序的配置，大约会带来 10%的性能损耗。排序方法如下：

```go
import "github.com/bytedance/sonic"
import "github.com/bytedance/sonic/encoder"

// Binding map only
m := map[string]interface{}{}
v, err := encoder.Encode(m, encoder.SortMapKeys)

// Or ast.Node.SortKeys() before marshal
var root := sonic.Get(JSON)
err := root.SortKeys()
```

### HTML Escape

标准库中默认会开启 html Escape，而 Sonic 出于性能损耗默认不开启

```go
func TestEncode(t *testing.T) {
	data := map[string]string{"&&": "<>"}
	// 标准库
	var w1 = bytes.NewBuffer(nil)
	enc1 := json.NewEncoder(w1)
	err := enc1.Encode(data)
	assert.NoError(t, err)
    // Sonic 库
	var w2 = bytes.NewBuffer(nil)
	enc2 := encoder.NewStreamEncoder(w2)
	err = enc2.Encode(data)
	assert.NoError(t, err)
	fmt.Printf("%v%v", w1.String(), w2.String())
}

// 运行结果：
{"\u0026\u0026":"\u003c\u003e"}
{"&&":"<>"}
```

若需要开启，可以通过下面的方法：

```go
import "github.com/bytedance/sonic/encoder"

v := map[string]string{"&&":"<>"}
ret, err := encoder.Encode(v, EscapeHTML) // ret == `{"\u0026\u0026":{"X":" \u003e"}}`

enc := encoder.NewStreamEncoder(w)
enc.SetEscapeHTML(true)
err := enc.Encode(obj)
```

### 大型模式问题

由于 Sonic 使用 golang-asm 作为 JIT 汇编器，这不太适合运行时编译，因此首次运行大型模式可能会导致请求超时甚至处理 OOM。为了获得更好的稳定性，建议在 Marshal（）/Unmarshal（）之前使用 Pretouch（）来处理大型模式或紧凑内存应用程序。

```go
import (
    "reflect"
    "github.com/bytedance/sonic"
    "github.com/bytedance/sonic/option"
)

func init() {
    var v HugeStruct

    // For most large types (nesting depth <= option.DefaultMaxInlineDepth)
    err := sonic.Pretouch(reflect.TypeOf(v))

    // with more CompileOption...
    err := sonic.Pretouch(reflect.TypeOf(v),
        // If the type is too deep nesting (nesting depth > option.DefaultMaxInlineDepth),
        // you can set compile recursive loops in Pretouch for better stability in JIT.
        option.WithCompileRecursiveDepth(loop),
        // For a large nested struct, try to set a smaller depth to reduce compiling time.
        option.WithCompileMaxInlineDepth(depth),
    )
}
```

# 小结

综上，选型上需要根据具体情况、不同领域的业务使用场景和发展趋势进行选择，综合考虑各方面因素。

例如：业务也只是简单的解析 http 请求返回的 JSON 串的部分字段，并且字段都是确定的，偶尔需要搜索功能，那 Gjson 是很不错的选择。

最后，不得不承认，从性能和功能总体而言，Sonic 的表现的确很亮眼。

其次，对于 cpu 密集性的操作的优化提供一种“野路子”：通过编写高性能的 C 代码并经过优化编译后供 golang 直接调用。实际上 Go 源码中的一些 cpu 密集型操作也编译成了汇编，如 crypto 和 math。

# 参考资料

[深入 Go 中各个高性能 JSON 解析库](https://www.luozhiyun.com/archives/535)

[Go 语言原生的 json 包有什么问题？如何更好地处理 JSON 数据？ ](https://cloud.tencent.com/developer/article/1820473)

[sonic ：基于 JIT 技术的开源全场景高性能 JSON 库](https://mp.weixin.qq.com/s?__biz=MzI1MzYzMjE0MQ==&mid=2247491325&idx=1&sn=e8799316d55c0951b0b54b404a3d87b8&scene=21#wechat_redirect)

[sonic/INTRODUCTION.md at main · bytedance/sonic](https://github.com/bytedance/sonic/blob/main/INTRODUCTION.md)

[sonic package - github.com/bytedance/sonic - Go Packages](https://pkg.go.dev/github.com/bytedance/sonic@v1.8.3#section-readme)

[goccy/go-json: Fast JSON encoder/decoder](https://github.com/goccy/go-json#how-it-works)

[【后台技术】为字节节省数十万核的 json 库 sonic](https://zhuanlan.zhihu.com/p/586050976)

# 课后思考

- 为什么 Go 不使用主流汇编，而是小众的 plan9 汇编？
- Sonic 本身有哪些局限性？
