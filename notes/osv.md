我们之前的很多工作都是基于IncludeOS的，但是IncludeOS的文档落后许多，而且开发上有很多限制（不能随心所欲地调用标准库），我便另外调研了一下OSv。

总的来说，OSv最大程度保留了Linuv的API，许多程序可以无修改地移植到OSv上，这样我们的开发难度会低很多。代价就是，用OSv打包到程序会比IncludeOS这类Unikernel更臃肿，启动时间更长。

由于OSv移植方便，且支持多种编程语言，我觉得它更可能促进Web应用部署由Container转向Unikernel（而不是IncludeOS、mirageOS这类移植很不方便的工具），毕竟计算机历史上很多变革靠的都不是表现“最优”的新技术，而是那些与旧技术兼容性更好、迁移更容易而表现不差的新技术。

考虑OSv的启动时间的话，qemu/kvm需800ms左右，[firecracker](https://github.com/firecracker-microvm/firecracker)/kvm需200ms左右（firecracker可以看作是一个特定领域的VMM）。其实IncludeOS用qemu/kvm启动的话也需要200-300ms，不过IBM Research做了一款更轻量的VMM——solo5，据称可以将这个时间缩短至10ms（而这是起初我们对所有Unikernel的期望）。然而之后IncludeOS的并没有对solo5做进一步的支持，因此目前solo5仅可以用来运行mirageOS（但显然我们不打算去写OCaml）。

所以目前我的建议是，先使用OSv进行我们的项目，完成后再根据表现考虑是否需要切换到clean-slate的Unikernel（IncludeOS或mirageOS）

一下是我总结的OSv使用方法，也可以直接参考https://github.com/cloudius-systems/osv

环境：ubuntu20.04（至少是19.10）

需要支持虚拟化（要有/dev/kvm这个设备），如果你是在虚拟机上跑的linux，你可以找找有没有“启用虚拟化管理程序”、“提供Intel VT-x支持”类似的选项。

```shell
#下载仓库并安装需要的包
git clone https://github.com/cloudius-systems/osv.git
cd osv && git submodule update --init --recursive
sudo ./scripts/setup.py

#这样做之后编译就不需要加多线程选项了
export MAKEFLAGS=-j$(nproc)
#编译一个helloworld（每次编译生成的镜像都放在./build/release/usr.img）
./scripts/build image=native-example

#运行（使用qemu/kvm）
./scripts/run.py
#运行（使用firecracker/kvm，首次运行会自动下载firecracker）
./scripts/firecracker.py

#编译一个nginx试试
./scripts/build image=nginx
#运行（我暂时还没调试清楚qemu的网络配置，这里就只用firecracker了）
./scripts/firecracker.py -n
#之后的输出里面会有ip地址，打开浏览器访问应该就能看到nginx的欢迎界面了
#另外我也还没搞清楚firecracker怎么退出，所以现在只能用kill
```



和其它Unikernel一样，OSv也不支持多进程，但支持多线程

https://github.com/cloudius-systems/osv/wiki/OSv-Linux-ABI-Compatibility

比如说，可以直接把lab3-1中的双人聊天室程序打包成镜像：

```shell
#先把tests/test-thread文件夹放到osv/apps中
#当前目录为osv仓库
./scripts/build image=test-thread
./scripts/firecracker.py -n
#输出里会有ip地址，然后可以像lab3时通过“nc <ip地址> 6666”来测试
#不同的是，这次相当于和一台VM通信
```

通过这种方式创建OSv通常需要准备几个文件（参见test-thread中的内容）

- 源码和Makefile：不言自明
- usr.manifest：指示如何部署所需文件到OSv镜像中，格式为<镜像中位置>: <主机中位置>
- module.py：主要是声明与其它模块之间的依赖关系、运行时的配置