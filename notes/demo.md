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

可能需要进一步学习express用法，https://github.com/expressjs/express

## PS

express是一个实用的nodejs网络框架