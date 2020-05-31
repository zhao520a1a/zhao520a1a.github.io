---
tags: [Go入门]    
categories: Go 

---
![77db407342d98de1dbfe6016af86c359](GO代码风格总结（私藏）.resources/132.jpeg)

### 指导原则

##### 几乎不需要指向接口类型的指针

##### interface的合理性验证

```go
var _ http.Handler = (*Handler)(nil)
```

##### 指针可以调用值方法！

##### 内部状态的 slices 或 maps输入输出要复制

##### Channel 的 size 要么是 1，要么是无缓冲的，其他尺寸要严格审查

##### 使用defer释放资源

``` go
p.Lock()
defer p.Unlock()
```

Defer 的开销非常小，只有在您可以证明函数执行时间处于纳秒级的程度时，才应避免这样做。使用 defer 提升可读性是值得的。
Channel 的 size 要么是 1，要么是无缓冲的。其他尺寸都必须经过严格的审查。

##### 枚举通常从1开始

变量空值为0，因此枚举从 1 开始, 除非使用零值是有意义的，如:当零值是理想的默认行为时。
const (
  Add int = iota + 1
  Subtract
  Multiply
)

##### 使用 [sync/atomic](https://golang.org/pkg/sync/atomic/) 包的原子操作对原始类型 (`int32`, `int64`等）进行操作

##### 使用选择依赖注入方式避免使用可变的全局变量

##### 避免在公共结构中嵌入类型

原因：这些嵌入的类型泄漏实现细节、禁止类型演化和模糊的文档。

- 嵌入式结构

 请避免在具体的列表实现中嵌入 `AbstractList`，需要手动将方法写入具体的列表，该列表将委托给抽象列表。

```go
//`AbstractList` 实现了多种列表类型
type AbstractList struct {}
// 添加将实体添加到列表中。
func (l *AbstractList) Add(e Entity) {
  // ...
}
// 移除从列表中移除实体。
func (l *AbstractList) Remove(e Entity) {
  // ...
}

// ConcreteList 是一个实体列表。
type ConcreteList struct {
  *AbstractList
}
```



- 嵌入接口  兼容的抽象列表 *interface*

``` go
// AbstractList 是抽象列表interface，有各种实体列表的通用实现。虽然将为开发人员提供更大的灵活性来改变未来，但仍然泄露了具体列表使用抽象实现的细节。
type AbstractList interface {
  Add(Entity)
  Remove(Entity)
}
// ConcreteList 是一个实体列表。
type ConcreteList struct {
  AbstractList
}
```

好的方式：


```go
// ConcreteList 是一个实体列表。
type ConcreteList struct {
  list *AbstractList
}
// 添加将实体添加到列表中。
func (l *ConcreteList) Add(e Entity) {
  return l.list.Add(e)
}
// 移除从列表中移除实体。
func (l *ConcreteList) Remove(e Entity) {
  return l.list.Remove(e)
}
```

无论是使用嵌入式结构还是使用嵌入式接口，嵌入式类型都会限制类型的演化.

- 向嵌入式接口添加方法是一个破坏性的改变。
- 删除嵌入类型是一个破坏性的改变。
- 即使使用满足相同接口的替代方法替换嵌入类型，也是一个破坏性的改变。

尽管编写这些委托方法是乏味的，但是额外的工作隐藏了实现细节，留下了更多的更改机会，还消除了在文档中发现完整列表接口的间接性操作。

减少嵌入类型，这是一种方便，可以帮助您避免编写冗长的委托方法。



##### 如何声明错误

如果不需要额外信息的简单错误,则使用errors.New 足够了。
如果客户需要检测并处理此错误，则使用自定义类型并实现该 Error() 方法。
如果正在传播下游函数返回的错误，则使用错误包装Error Wrapping 手法
如果调用者不需要检测或处理的特定错误情况或其他情况，则使用 fmt.Errorf。
在生产环境中运行的代码必须避免出现 panic，避免级联失败，函数要返回Error

##### 不要panic

- panic/recover 不是错误处理策略。仅当发生不可恢复的事情（例如：nil 引用）时，程序才必须 panic。但是，程序初始化是一个例外。

- 即使在测试代码中，也优先使用`t.Fatal`或者`t.FailNow`而不是 panic 来确保失败被标记。



##### 用time处理时间

使用time.Time表达时间点，使用time.duration表达时间段。

对外部系统使用 `time.Time` 和 `time.Duration`

##### 不需要指向 `sync.Mutex` 和 `sync.RWMutex` 的指针，因为零值 `sync.Mutex` 和 `sync.RWMutex` 是有效的。



### 性能

##### 优先使用 strconv 而不是 fmt

``` go
strconv.Itoa(rand.Int())
```

##### 不要反复从固定字符串创建字节 slice,避免字符串到字节的重复转换

##### 尽可能初始化时指定 Map 容量

##### 尽可能的使用字符代替字符串

##### 尽可能的使用切片代替数组

##### 尽可能的使用数组和切片代替映射 ，但当数组元素是稀疏的（例如有很多 `0` 值或者空值 `nil`），使用映射会降低内存消耗

##### 尽可能的使用 `for range` 去遍历切片

##### 尽可能在需要分配大量内存时使用缓存

##### 当定义一个方法时，使用指针类型作为方法的接受者

### 规范

##### 相似的声明放在一组，将不相关的分开声明（适用于常量、变量、类型声明，且分组使用的位置没有限制）

```go
import (
	"a"
  "b"
)
const (
	a = 1
  b = 2
)
var (
 a = 1
 b = 1
)
type {
  Area float64
  Volume float64
}

```

##### import 分组

导入应该分为两组：

- 标准库
- 其他库

##### 导入别名

除非导入之间有直接冲突 或 程序包名称与导入路径的最后一个元素不匹配，否则应避免导入别名。

``` go 
import (
  "fmt"
  "os"
  "runtime/trace"

  nettrace "golang.net/x/trace"
  client "example.com/client-go"
  trace "example.com/trace/v2"
)
```



##### 函数分组与顺序

- 函数应按粗略的调用顺序排序，导出的函数应先出现在文件中，newXXX()在定义类型之后和其他方法之前；普通工具函数应在文件末尾；
- 同一文件中的函数应按接收者分组。

``` go 
//按接收者分组
type something struct{ ... }

func newSomething() *something {
    return &something{}
}

func (s *something) Cost() {
  return calcCost(s.weights)
}

func (s *something) Stop() {...}

func calcCost(n []int) int {...}
```

##### 减少嵌套

尽可能先处理错误情况/特殊情况并尽早返回或继续循环来减少嵌套，即：*先处理错误情况*

``` go 
//Bad Code
for _, v := range data {
  if v.F1 == 1 {
    v = process(v)
    if err := v.Call(); err == nil {
      v.Send()
    } else {
      return err
    }
  } else {
    log.Printf("Invalid v: %v", v)
  }
}

// Good Code
for _, v := range data {
  if v.F1 != 1 {
    log.Printf("Invalid v: %v", v)
    continue
  }

  v = process(v)
  if err := v.Call(); err != nil {
    return err
  }
  v.Send()
}
```

##### 减少不必要的 else

##### 缩小变量作用域

如果有可能，尽量缩小变量作用范围。除非它与 [减少嵌套](https://github.com/xxjwxc/uber_go_guide_cn#减少嵌套)的规则冲突。

例外：`如果需要在 if 之外使用函数调用的结果，则不应尝试缩小范围。`

```go
//Bad Code
err := ioutil.WriteFile(name, data, 0644)
if err != nil {
 return err
}

//Good Code 
if err := ioutil.WriteFile(name, data, 0644); err != nil {
 return err
}

```



##### 顶层变量声明

使用标准`var`关键字。请勿指定类型，除非它与表达式的类型不同。

##### 对于未导出的顶层常量和变量，使用_作为前缀

使它们在使用时明确表示它们是全局符号。

例外：未导出的错误值，应以`err`开头。

##### 本地变量声明采用(:=)

例外：在某些情况下，`var` 使用关键字时默认值会更清晰。例如，声明空切片。

##### `nil` 是一个有效的长度为 0 的 slice

- 函数返回值：应该用nil 来代替空切片[]int{}；

- 始终使用`len(s) == 0`检查切片是否为空，而非 `nil`。

- 用var声明空切片，不需要创建

  ```go
  var nums []int
  // nums := []int{}
  // nums := make([]int)
  ```

##### 调用函数时，避免参数语义不明确

函数调用中的意义不明确的参数可能会损害可读性，此时，请为参数添加注释 (`/* ... */`)

```go
// func printInfo(name string, isLocal, done bool)
printInfo("foo", true /* isLocal */, true /* done */)
```

而更好的处理方式是将上面的 `bool` 类型换成自定义类型，明确了语义且增加了灵活性。

``` go 
type Region int

const (
  UnknownRegion Region = iota
  Local
)

type Status int

const (
  StatusReady Status= iota + 1
  StatusDone
  //未来可以灵活添加状态
)

func printInfo(name string, region Region, status Status)
```

##### 避免转义，使用 " ` "原生字符串

也就是 " ` " 来表示原生字符串，在需要转义的场景下，我们应该尽量使用这种方案来替换。

可以避免更难阅读的手工转义的字符串。

``` go
//wantError := "unknown name:\"test\""
wantError := `unknown error:"test"`
```

##### 嵌入式字段位置

嵌入式字段应位于结构体字段列表顶部，用一个空行与常规字段分割开。

##### 初始化结构体指定字段名称

初始化结构体时，几乎始终应该指定字段名称。

例外：如果有 3 个或更少的字段，则可以在测试表中省略字段名称。

##### 初始化 Struct 引用，使用`&T{}`代替`new(T)`

##### 初始化 Maps，大都使用 `make(..)`

空map初始化使用make(..)，尽可能提供map容量大小。好处：令map声明和初始化看起来差别非常大。

例外：如果 map 包含`固定的元素列表`，则使用 map literals(map 初始化列表) 初始化映射。

```go
var (
  m1 map[T1]T2 //声明m1，为初始化，写入时会 panic；
 // m2 = map[T1]T2{}  
  m2 = make(map[T1]T2) //初始化m2，m2读写安全;
  m3 = map[T1]T2{
  k1: v1,
  k2: v2,
  k3: v3,
}
) 
```



 ##### 函数外声明格式化字符串的格式，请将其设置为`const`常量。

```go
const msg = "unexpected values %v, %v\n"

fmt.Printf(msg, 1, 2)
```





### 命名

#### 包名

当命名包时，请按下面规则选择一个名称：

- 全部小写。没有大写或下划线。
- 大多数使用命名导入的情况下，不需要重命名。
- 简短而简洁。(请记住，在每个使用的地方都完整标识了该名称。)
- 不用复数。例如`net/url`，而不是`net/urls`。
- 不要用“common”，“util”，“shared”或“lib”。这些是不好的，信息量不足的名称。

#### 函数名

当某个函数需要被外部包调用的时候才使用大写字母开头，并遵循 Pascal 命名法；
否则就遵循骆驼命名法，即第一个单词的首字母小写，其余单词的首字母大写。

- 返回某个对象的函数或方法的名称一般都是使用名词，没有 Get... 之类的字符。
- 修改某个对象，则使用 SetName，有必须要的话可以使用大小写混合的方式，如 MixedCaps 或 mixedCaps，而不是使用下划线来分割多个名称。

例外：为了对相关的测试用例进行分组，函数名可能包含下划线，如：`TestMyFunction_WhatIsBeingTested`.

#### 变量名

- 变量的命名规则遵循骆驼命名法，即首个单词小写，每个新单词的首字母大写，例如：numShips 和 startDate，但如果你的全局变量希望能够被外部包所使用，则需要将首个单词的首字母也大写
- 对于布尔值而言，建议以 is 或者 Is 开头的 isSorted、isFinished、isVisible


#### 接口名

接口的名字由方法名加 [e]r 后缀组成，
例如 Printer、Reader、Writer、Logger、Converter 等等。
还有一些不常用的方式（当后缀 er 不合适时），比如 Recoverable，此时接口名以 able 结尾，或者以 I 开头（像Java 中那样）。

#### 错误类型

错误类型以 “Error” 结尾
错误变量以 “err” 或 “Err” 开头。


#### panic

标准库中有许多包含` Must 前缀`的函数，像 regexp.MustComplie 和 template.Must；即当正则表达式或模板中转入的转换字符串导致错误时，这些函数会 panic。

#### 测试

文件名满足这种形式 *_test.go
测试文件中必须导入 "testing" 包，并写一些名字以 TestZzz 打头的全局函数，这里的 Zzz 是被测试函数的字母描述，如 TestFmtInterface，TestPayEmployees 等。

``` go 
func TestAbcde(t *testing.T)
```



> 参考资料：
>
> [uber-go/guide](https://github.com/xxjwxc/uber_go_guide_cn)
>
> [the-way-to-go](https://github.com/Unknwon/the-way-to-go_ZH_CN)

