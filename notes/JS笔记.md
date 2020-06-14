语法类似java。

语句结尾可以有分号，也可以没有，但是推荐加上分号。

语义与缩进无关。

JS默认对于各类错误有较大的容忍度。可以使用strict模式防止部分语法错误导致的意想不到的行为。例如：

ES6为较新的标准，部分浏览器可能不支持。

### Hello World

在网页输出提示：

`alert("Hello World!");`

在控制台输出：

`console.log("Hello World!");`

### 比较运算符

JavaScript在设计时，有两种比较运算符：
第一种是`==`比较，它会自动转换数据类型再比较，很多时候，会得到非常诡异的结果；
第二种是`===`比较，它不会自动转换数据类型，如果数据类型不一致，返回`false`，如果一致，再比较。
由于JavaScript这个设计缺陷，不要使用==比较，始终坚持使用===比较。
另一个例外是NaN这个特殊的Number与所有其他值都不相等，包括它自己：
`NaN === NaN; // false`
唯一能判断NaN的方法是通过isNaN()函数：
`isNaN(NaN); // true`

### null与undefined

`null`表示一个“空”的值，`undefined`表示值未定义。大多数情况下，我们都应该用`null`。`undefined`仅仅在判断函数参数是否传递的情况下有用。

### 变量

`var`表示声明变量。命名空间性质与Python相同，具有闭包等特性。不在函数内声明的变量为全局变量。

```javascript
var a = 1;
a = 'xyz';
```

JavaScript在设计之初，为了方便初学者学习，并不强制要求用`var`申明变量。这个设计错误带来了严重的后果：如果一个变量没有通过`var`申明就被使用，那么该变量就自动被申明为全局变量。

可以启用strict模式防止发生该情况，方法是在JavaScript代码的第一行写上：

```
'use strict';
```

该模式下不经过var声明便使用变量会报错。

`const`关键字可以用来定义常量。(ES6)


### Array

可以包括任意数据类型，类似于Python中的list。

```javascript
[1, 2, 3.14, 'Hello', null, true]
```

```javascript
new Array(1, 2, 3); // 创建了数组[1, 2, 3]
```

索引越界不会报错：

```javascript
var arr = [1, 2, 3];
arr[5] = 'x';
arr; // arr变为[1, 2, 3, undefined, undefined, 'x']
```

常用成员：

```javascript
length		//长度
indexOf()	//某元素第一次出现的位置
slice()		//取子列表
push()/pop()	//在尾部添加或删除
unshift()/shift()	//在头部添加或删除
sort()		//排序
reverse()		//翻转
splice()		//删改的万能方法
concat()		//拼接(返回新的array，而非原位修改)
join()		//类似于Python中字符串的join方
```

### 字符串

用`''`或`""`包起来。

也可以使用反引号表示多行字符串(ES6标准)。

```javascript
`这是一个
多行
字符串`;
```

字符串拼接：` "Hello"+"world"`

模板字符串(ES6标准)：

```javascript
var a = 1;
var s = `Number : ${a}`	;	//注意使用反引号
```

和Python一样，字符串是不可变对象：

```javascript
var s = 'Test';
s[0] = 'X';
alert(s); // s仍然为'Test'
```

### 对象

由key-value对组成的无序集合。key都是字符串类型，value可以是任意数据类型。

```javascript
var person = {
    name: 'Bob',
    age: 20,
    tags: ['js', 'web', 'mobile'],
    city: 'Beijing',
    hasCar: true,
    'zip-code': null
};
```
(key一般可以不用引号包起来，除非其包含某些特殊字符，例如`-`)

获取对象的属性：

```javascript
person.name;
person.['name'];
person['zip-code'];	//包含特殊字符时只能使用这种方式
person.cv;	//没有cv属性，返回undefined
```

所有对象都最终继承于`object`

判断对象是否具有某属性：

```javascript
'toString' in person;	//包括了继承来的属性，因为object有该属性，所以返回true
person.hasOwnProperty('toString');	//不包括继承来的属性，因此返回false
```

### Map(ES6)

类似于Python中的dictionary。key和value都可以是任意类型。

```javascript
var m = new Map([['a',1],['b',2],['c',3]]);
m.get('a');	// 1
m.set('d',4);	//设置新的key-value
m.delete('d');	//删除key-value
m.has('e');		//检查是否有该key
```

### Set(ES6)

与Python中的set相同。

```javascript
var s = new Set([1,2,3,3,4]);
s;	// 1,2,3,4
s.add(5)
s.delete(5)
```

### 分支与循环

分支：

+ if ... else ... ，与C相同。

循环：

+ for(...;...;...)
+ for(... in ...)	//遍历对象的属性名称
+ for(... of ...)	//遍历iterable类型的内容(ES6)，也可用forEach方法替代(ES5.1)
+ while()
+ do ... while(...);

### 函数

“头等公民”，可以像变量一样使用。

```javascript
function plus(x, y){		//函数名可以省略，成为匿名函数
    return x+y;
}
var func = plus;
plus(1,2,3);	//多传入的参数不影响调用，返回3
plus(1);	//传入的参数少了也不影响调用，返回NaN，此时形参y为undefined

function _plus(x, y){
    //arguments关键字表示传入函数的所有参数，具有length成员，类似于Array，但不是Array
    return arguments[0]*arguments[1];
}

function foo(x, y, ...rest){
    //rest关键字为接受多余参数的Array
    console.log(x);
    console.log(y);
    console.log(rest);
}
foo(1, 2, 3, 4, 5);
// 结果:
// a = 1
// b = 2
// Array [ 3, 4, 5 ]

foo(1);
// 结果:
// a = 1
// b = undefined
// Array []		//注意这里rest不是undefined
```
函数对象具有apply方法，用于定义装饰器。

### 命名空间与作用域

JavaScript的函数定义有个特点，它会先扫描整个函数体的语句，把所有申明的变量“提升”到函数顶部(即所有var语句)。但是不建议先使用后声明。

全局变量实际都会绑定为全局对象`window`的一个属性。

JavaScript实际上只有一个全局作用域。任何变量（函数也视为变量），如果没有在当前函数作用域中找到，就会继续往上查找，最后如果在全局作用域中也没有找到，则报`ReferenceError`错误。

for循环等语句块中是无法用`var`定义具有局部作用域的变量。可以使用`let`关键字(ES6)定义代替`var`的位置来定义块级作用域变量。

### 解构赋值(ES6)
```javascript
var [x, y, z] = ['hello', 'JavaScript', 'ES6'];
let [x, [y, z]] = ['hello', ['JavaScript', 'ES6']];
let [, , z] = ['hello', 'JavaScript', 'ES6']; // 忽略前两个元素

var person = {
    name: '小明',
    age: 20,
    gender: 'male',
    passport: 'G-12345678',
    school: 'No.4 middle school',
    address: {
        city: 'Beijing',
        street: 'No.1 Road',
        zipcode: '100001'
    }
};
var {name, address: {city, zip}} = person;
let {passport:id} = person;	//将passport属性的值给变量id
var {single=true} = person;	//默认值，否则不存在的属性会返回undefined
```

这是因为JavaScript引擎把{开头的语句当作了块处理，于是=不再合法。解决方法是用小括号括起来：
```javascript
// 声明变量:
var x, y;
// 解构赋值:
{x, y} = { name: '小明', x: 100, y: 200};
// 语法错误: Uncaught SyntaxError: Unexpected token =

({x, y} = { name: '小明', x: 100, y: 200});	//正确做法
```

变量交换：
```javascript
[x, y] = [y, x]
```

快速获取当前页面的域名和路径：

```javascript
var {hostname:domain, pathname:path} = location;
```

### 箭头函数(ES6)

类似于Python的lambda表达式，用于定义匿名函数：

```javascript
x => x * x
//相当于：
function (x) {
    return x * x;
}
(x, y) => x * x + y * y
(x, y, ...rest) => x * x + y * y
() => 3.14
x => {
    if (x > 0) 
        return x * x;
    else
        return - x * x;
}
x => { foo: x }		//SyntaxError，因为和函数体的{ ... }有语法冲突
x => ({ foo: x })
```

箭头函数内部的`this`是词法作用域，由上下文确定。

### generator(ES6)

与Python类似，使用yield关键字。

具有next()方法。

iterable

generator还有另一个巨大的好处，就是把异步回调代码变成“同步”代码。这个好处要等到后面学了AJAX以后才能体会到。