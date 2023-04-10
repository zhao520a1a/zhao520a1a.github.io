---
title: Go读取Excel数据
tags: [go]
categories: [踩坑记录]
date: 2021-09-20
cover: https://raw.githubusercontent.com/qax-os/excelize/7c221cf29531fcd38871d3295f4b511029cb4282/excelize.svg
---

> 大家好，我是Golden，一个努力谋生的工具人！
>
> 引言：最近工作过程中，有需求要将excel中的图片上传到公司的OSS存储服务器。
>
> 经过一个下午的探索，已经将需求搞定了，开心的一批😊！
>
> 下面将自己在踩坑过程记录一下，分享给有需要的小伙伴哈，拿走不谢。。



#### 问题1：Go中有可以读取的excel文件中图片的工具包呢？

通过在Github中搜索，找到了一个功能丰富且强大的Excel工具类👍；废话不多说，上地址：

GitHub地址: https://github.com/360EntSecGroup-Skylar/excelize

码云地址: https://gitee.com/xurime/excelize  （鉴于有些小伙伴，访问github慢，特此提供）

简介：[Excelize](https://links.jianshu.com/go?to=https%3A%2F%2Fgithub.com%2F360EntSecGroup-Skylar%2Fexcelize) 是 Go 语言编写的一个用来操作 Office Excel 文档类库，基于 ECMA-376 Office OpenXML 标准。可以使用它来读取、写入 XLSX 文件。相比较其他的开源类库，Excelize 支持写入原本带有图片(表)的文档，还支持向 Excel 中插入图片，并且在保存后不会丢失图表样式。



####  问题2：如何使用的，有帮助文档吗?

帮助文档：https://xuri.me/excelize/zh-hans/stream.html#Flush

由于支持许多功能，在这里就不一一列举了，详细使用文档以及获取后期的维护更新可以从项目的主页获取。下面👇我主要介绍两个功能**创建图表** 和**插入图片**

> 介于有些小伙伴可能比较懒， (⊙o⊙)…不对，是比较忙；我早都想到了， 为了方便大家查看，写个粗糙的demo的，Demo地址：https://github.com/zhao520a1a/go-practice-demo.git/src/guide/testExcel.go 中。当然更建议有空看官方文档，也费不了多少时间。

###  使用方式

#### 安装

  ```
  go get github.com/360EntSecGroup-Skylar/excelize
  ```

- 如果您使用 [Go Modules](https://blog.golang.org/using-go-modules) 管理软件包，请使用下面的命令来安装最新版本。

  ```
  go get github.com/360EntSecGroup-Skylar/excelize/v2
  ```

#### 在 Excel 文档中创建图表

使用 Excelize 生成图表十分简单，仅需几行代码。您可以根据工作表中的已有数据构建图表，或向工作表中添加数据并创建图表

![Excelize](https://gitee.com/xurime/excelize/raw/master/test/images/chart.png)

```Go
package main

import (
    "fmt"

    "github.com/360EntSecGroup-Skylar/excelize"
)

func main() {
    categories := map[string]string{"A2": "Small", "A3": "Normal", "A4": "Large", "B1": "Apple", "C1": "Orange", "D1": "Pear"}
    values := map[string]int{"B2": 2, "C2": 3, "D2": 3, "B3": 5, "C3": 2, "D3": 4, "B4": 6, "C4": 7, "D4": 8}
    f := excelize.NewFile()
    for k, v := range categories {
        f.SetCellValue("Sheet1", k, v)
    }
    for k, v := range values {
        f.SetCellValue("Sheet1", k, v)
    }
    if err := f.AddChart("Sheet1", "E1", `{"type":"col3DClustered","series":[{"name":"Sheet1!$A$2","categories":"Sheet1!$B$1:$D$1","values":"Sheet1!$B$2:$D$2"},{"name":"Sheet1!$A$3","categories":"Sheet1!$B$1:$D$1","values":"Sheet1!$B$3:$D$3"},{"name":"Sheet1!$A$4","categories":"Sheet1!$B$1:$D$1","values":"Sheet1!$B$4:$D$4"}],"title":{"name":"Fruit 3D Clustered Column Chart"}}`); err != nil {
        fmt.Println(err)
        return
    }
    // 根据指定路径保存文件
    if err := f.SaveAs("Book1.xlsx"); err != nil {
        fmt.Println(err)
    }
}
```

#### 向 Excel 文档中插入图片

```go
package main

import (
    "fmt"
    _ "image/gif"
    _ "image/jpeg"
    _ "image/png"

    "github.com/360EntSecGroup-Skylar/excelize"
)

func main() {
    f, err := excelize.OpenFile("Book1.xlsx")
    if err != nil {
        fmt.Println(err)
        return
    }
    // 插入图片
    if err := f.AddPicture("Sheet1", "A2", "image.png", ""); err != nil {
        fmt.Println(err)
    }
    // 在工作表中插入图片，并设置图片的缩放比例
    if err := f.AddPicture("Sheet1", "D2", "image.jpg", `{"x_scale": 0.5, "y_scale": 0.5}`); err != nil {
        fmt.Println(err)
    }
    // 在工作表中插入图片，并设置图片的打印属性
    if err := f.AddPicture("Sheet1", "H2", "image.gif", `{"x_offset": 15, "y_offset": 10, "print_obj": true, "lock_aspect_ratio": false, "locked": false}`); err != nil {
        fmt.Println(err)
    }
    // 保存文件
    if err = f.Save(); err != nil {
        fmt.Println(err)
    }
}
```


#### 关于图片缩放的一点建议（来源网友建议，本人为亲自实验）

推荐使用一个开源库(github.com/nfnt/resize)，不要使用该库自带的缩放，会有一点问题
并且先对单元格做大小控制，再插入图片，否则有可能会导致一些图片被拉伸


> 喜欢即可关注，关注即可进步。Over!

