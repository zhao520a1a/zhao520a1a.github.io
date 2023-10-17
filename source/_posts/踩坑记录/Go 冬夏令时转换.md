---
title: Go读取Excel数据
tags: [go]
categories: [踩坑记录]
date: 2021-03-20
cover: https://raw.githubusercontent.com/qax-os/excelize/7c221cf29531fcd38871d3295f4b511029cb4282/excelize.svg
---

## 引言

需求：给定一个时间戳 + 时区(Asia/shanghai) + 输出格式，返回该时区下特定格式的时间字符串

注意：一定需要考虑到不同国家冬夏令时情况

抽象一下：难点在于不同时区不同夏令时(夏时制)间转换

## 基本概念

### 夏时令

夏季人为将时间调快一小时，英文为Daylight Saving Time，简称DST

### 冬令时

冬季人为把时针拨回一小时

注意：大多数时候，也会将冬夏令时，统称为夏令时

影响：夏天的时候，中国的北京时间（东八区）与美国太平洋时区（西八区）的时差是15小时，而到了冬天却变成16小时。

各个国家和地区的时区规则，请参见[此处的列表](https://stackoom.com/link/aHR0cHM6Ly9lbi53aWtpcGVkaWEub3JnL3dpa2kvTGlzdF9vZl90el9kYXRhYmFzZV90aW1lX3pvbmVz) 。

实时查询各个国家和地区时间，请参见[该网站](http://zh.thetimenow.com/utc/coordinated_universal_time)

## 官方支持

官方包中提供了[time.LoadLocation](https://stackoom.com/link/aHR0cHM6Ly9nb2xhbmcub3JnL3BrZy90aW1lLyNMb2FkTG9jYXRpb24=)可以完成以上的需求；

```go
const TIME_LAYOUT = "2006-01-02 15:04:05"

func parseWithLocation(name string, timeStr string) (time.Time, error) {
	locationName := name
	if l, err := time.LoadLocation(locationName); err != nil {
		println(err.Error())
		return time.Time{}, err
	} else {
		//zone, offset := time.Now().In(location).Zone()
		lt, err := time.ParseInLocation(TIME_LAYOUT, timeStr, l)
		if err != nil {
			println(err.Error())
		}
		fmt.Println(locationName, lt)
		return lt, nil
	}
}
```

> 具体是如何完成呢？

首先开源库 [IANA TZDB](https://www.iana.org/time-zones)提供`时区ID`到`具体夏令时偏移量`的转换数据，

然后Go源码中包含了它所提供的数据包，因此可以判断冬夏令时的信息。

> Go语言提供的time.LoadLocation可能又有什么坑呢？

正如标准库文档中所说的:

> The time zone database needed by LoadLocation may not be present on all systems, especially non-Unix systems. LoadLocation looks in the directory or uncompressed zip file named by the ZONEINFO environment variable, if any, then looks in known installation locations on Unix systems, and finally looks in $GOROOT/lib/time/zoneinfo.zip.

LoadLocation所需的时区数据库可能并不存在于所有系统上,尤其是非unix系统. 如果有的话,LoadLocation查找由ZONEINFO环境变量命名的目录或未压缩的 `ZONEINFO` 环境变量命名的zip文件, 然后查找Unix系统上已知的安装位置,最后查找 `$GOROOT/lib/time/ZONEINFO.zip`.

上源码，可以清楚的看到在unix系统中，zoneSources的查找路径：

![be6f4b58613bf7a5828c4af73c95046f.png](evernotecid://CD3082B6-03A3-4D41-80AB-E48CAD259C0B/appyinxiangcom/17782910/ENResource/p1647)

因此不同国家政治策略的变动，时区对应关系会经常更新，IANA TZDB会发布新的[版本包](ftp://ftp.iana.org/tz/)，但是`Go并不会主动更新成最新的版本`，这导致可能会有问题。

肿么办？

可以升级到最新Go版本(里面会引入TZDB最新发布包)或者自己手动更新Go引用的TZDB的包。

脚本更新时可以参考官方给的[更新脚本](https://github.com/golang/go/tree/dev.boringcrypto.go1.15/lib/time)。

## 参考

[golang的时区和神奇的time.Parse](https://www.jianshu.com/p/f809b06144f7)

[在Go中处理时区](https://www.shuzhiduo.com/A/Vx5M24n3dN/)
