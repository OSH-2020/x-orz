# demo

## node-from-host

首先打包node-from-host

复制副本（主要是为了备份，不复制也没关系），将makefile中添加向usr.manifest写入keyvaluestore.js相关内容（注意冒号后面要加空格），并把js复制到目录下

向module.py写入运行相关内容

重新打包，运行unikernel，报错

```
Error: Cannot find module 'express'
    at Function.Module._resolveFilename (internal/modules/cjs/loader.js:636:15)
    at Function.Module._load (internal/modules/cjs/loader.js:562:25)
    at Module.require (internal/modules/cjs/loader.js:692:17)
    at require (internal/modules/cjs/helpers.js:25:18)
    at Object.<anonymous> (/keyvaluestore.js:1:17)
    at Module._compile (internal/modules/cjs/loader.js:778:30)
    at Object.Module._extensions..js (internal/modules/cjs/loader.js:789:10)
    at Module.load (internal/modules/cjs/loader.js:653:32)
    at tryModuleLoad (internal/modules/cjs/loader.js:593:12)
    at Function.Module._load (internal/modules/cjs/loader.js:585:3)
```

使用`npm install express`下载express依赖包，运行仍出错

估计是环境变量之类的问题，此处环境变量指osv中的环境，也有可能是osv中并没有把此模块打包等原因

看到有node-express-example示例，进行尝试

## node-express-example

由于osv本身的node示例似乎有点问题，将`/apps/node/node-8.11.2/out/Release/lib.target/libnode.so`复制到`/apps/node`目录下改名为 libnode-8.11.2.so

直接使用 build 脚本打包，运行示例程序正确

将keyvaluestore改名为index.js放到`/apps/node-express-example/ROOTFS/express/examples/hello_world`下，打包运行，仍然报错。

~~可能需要进一步学习express用法，https://github.com/expressjs/express~~

6.19进展：发现在上述操作之后把keyvaluestore.js(已更名为index.js)中

```javascript
var express = require('express')
```
改为

```javascript
var express = require('../../')
```

即可打包并正常运行，但是不知什么原因网络仍然是不可用的，就是说即使有下列输出：

```shell
wangyuanlong@ubuntu:~/osv$ ./scripts/run.py
OSv v0.55.0-13-gcf78fa9e
eth0: 192.168.122.15
Booted up in 593.49 ms
Cmdline: /libnode.so ./examples/hello-world
Running keyvaluestore on port:  9000
server is listening on 9000
```

但另起终端运行db.js，仍然会有类似：

```shell
wangyuanlong@ubuntu:~/osv-microservice-demo$ node db.js localhost:9000
Running db on port:  9001
Using keyvaluestore endpoint:  http://localhost:9000
Key-value store is not available
Key-value store is not available
Key-value store is not available
Key-value store is not available
Key-value store is not available
Key-value store is not available
Key-value store is not available
^C
```

的输出产生（但此处我并没有将db.js按上述方法打包，可以从文件路径上看到区别）

6.19更新

按照firecracker提供的地址访问是可以访问到的，至此完成打包，关于命令行参数只需改动项目目录（即osv/apps/xxx/）下module.py中的对应行即可。

```shell
wangyuanlong@ubuntu:~/osv$ ./scripts/firecracker.py -n
The tap interface fc_tap0 not found -> needs to set it up!
Setting up TAP device in natted mode!
[sudo] password for wangyuanlong: 
To make outgoing traffic work pass physical NIC name
OSv v0.55.0-13-gcf78fa9e
eth0: 172.16.0.2
Booted up in 231.57 ms
Cmdline: /libnode.so ./examples/hello-world  
Running keyvaluestore on port:  9000
server is listening on 9000

#在另一个终端中
wangyuanlong@ubuntu:~/osv-microservice-demo$ node db.js 172.16.0.2:9000
Running db on port:  9001
Using keyvaluestore endpoint:  http://172.16.0.2:9000
Database endpoint registered
Database is listening on 9001
#回到原来终端，产生输出

dbendpoint=172.16.0.1:9001
```

6.24更新

其它项目文件中有诸如`ip`，`os`等等依赖项，同时也用到了同目录下的common.js文件，具体的处理方式是：将common.js放在上述hello-world目录下，将需要打包运行的文件改名为index.js放在hello-world下，然后将需要的外部依赖放在`/apps/node-express-example/ROOTFS/express/node_modules`目录下（我的操作是直接把osv-microservice-demo项目目录下的`node_modules`目录全都复制到前面的目录下，重复部分跳过），记得index.js里的

```javascript
var express = require('express')
```
改为

```javascript
var express = require('../../')
```

（有可能不改也行，因为依赖项已经复制过来了，不过我没有尝试）

## PS

express是一个实用的nodejs网络框架