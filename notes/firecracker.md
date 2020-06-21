### 简介

Firecracker是一种新的虚拟化技术，基于kvm，使用Rust编写，旨在通过“低开销”实现“高隔离”，与传统的QEMU相比有很大优势，我们这里只关注其在OSv上的应用。

更多内容见Firecracker主页（https://firecracker-microvm.github.io/）和仓库

Firecracker启动OSv虚拟机至少需要以下资源：

- disk image：我们编译的OSv应用的镜像，OSv仓库默认存在 `build/release/usr.raw` 

  注意：这里Firecracker仅支持RAW格式的镜像，这一般很大，实践中应该更常使用QCOW2格式 `build/release/usr.img` ，不过通过下面的命令可以很快实现格式转换

  ```shell
  qemu-img convert -O raw <qcow_disk_path> <raw_disk_path>
  ```

- kernel loader：内核镜像？，OSv仓库默认存在 `/build/release/kernel.elf` ，与我们的应用源码无关

- 可能需要一些虚拟网络设备（事先配置好的tap或bridge）

- 启动参数（包括要运行的命令）

以上内容是针对原始的Firecracker程序而言，OSv仓库提供的firecracker.py和其它脚本方便了这个过程，但只能启动一台使用网络的VM，我之后会进行升级以满足我们启动多示例的需求

### 使用

Firecracker提供两种配置VM的方法：

- 使用 RESTful API（好像是一种命名管道）
- 使用配置文件（json格式）

简单起见我们先使用后者：

```shell
firecracker --no-api --config-file <配置文件>
```

上节提到的所有信息都写在这个配置文件中

另外我们需要让VM间通信，所以要事先配置好网络。Firecracker至少支持两种网络配置——natted和bridge，VM较多时bridge更贴合我们的需求，以两个VM为例：

```shell
# 以下命令均需要sudo

# 创建bridge并配置上IP
brctl addbr fc_br0
ip link set dev fc_br0 up
ip addr add 172.16.0.1/24 dev fc_br0
# 创建一个tap设备并和bridge相连（tap设备用作VM的虚拟网卡？）
ip tuntap add dev fc_tap0 mode tap
ip link set dev fc_tap0 up
brctl addif fc_br0 fc_tap0
# 另一个tap设备同理
ip tuntap add dev fc_tap1 mode tap
ip link set dev fc_tap1 up
brctl addif fc_br0 fc_tap1

# 转到tests/network目录下
# 把上面提到的kernel loader拷贝到kernel.elf
# 把nginx镜像（raw格式）拷贝到nginx.raw，curl镜像（raw格式）拷贝到curl.raw
firecracker --no-api --config-file config-nginx
firecracker --no-api --config-file config-curl

# 删除之前创建的网络设备（可选）
ip tuntap del dev fc_tap0 mode tap
ip tuntap del dev fc_tap1 mode tap
```

创建curl镜像的方法参考[OSv仓库](https://github.com/cloudius-systems/osv#building-osv-kernel-and-creating-images)

PS：以上搭建的都是实验环境，生产环境中可能需要更改

可能用到的技术： [NAT](http://www.zsythink.net/archives/1764) ， [tun/tap](https://segmentfault.com/a/1190000009249039) ， [veth](https://segmentfault.com/a/1190000009251098) ， [bridge](https://segmentfault.com/a/1190000009491002)

