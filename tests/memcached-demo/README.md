# Memcached demo

仓库中是改好的js文件以及编译好的memcached，运行memcached时使用命令

```
sudo ./memcached -u root -t1 -l 127.0.0.1 -p 9000 -m5000
```

其中 -p 指定端口，-l 指定 ip ，在unikernel中运行时去掉即可。memcached可以完全取代 keyvaluestore.js, 其他脚本与 keyvaluestore 交互的部分均改为了与 memcache 交互。

另外要运行memcached需要 libevent 库，在 node.js 中引入了 memcached 模块，故需要使用 npm 下载之，放在此目录下的 node_modules 目录下，osv-microservice-demo 的 node_modules 目录也要复制过来。由于这部分文件比较大，所以不放在仓库里了。

## 查看键下的值

要测试 memcached 可以使用 telnet 命令，以连接远程终端

```
$ telnet <ip> <port>
```

然后输入

```
get <key>
```

即可得到 key 对应的值，其他命令用法参见https://www.runoob.com/memcached/memcached-tutorial.html

