Firecracker是一种新的虚拟化技术，旨在通过“低开销”实现“高隔离”，与传统的QEMU相比有很大优势，我们这里只关注其在OSv上的应用。

更多内容见Firecracker主页（https://firecracker-microvm.github.io/）和仓库

Firecracker启动OSv虚拟机至少需要以下资源：

- disk image：我们编译的OSv应用的镜像，OSv仓库默认存在 `build/release/usr.raw` 

  注意：这里Firecracker仅支持RAW格式的镜像，这一般很大，实践中应该更常使用QCOW2格式 `build/release/usr.img` ，不过通过命令 `qemu-img convert -O raw <qcow_disk_path> <raw_disk_path>` 可以很快实现格式转换

- kernel loader：内核镜像？，OSv仓库默认存在 `/build/release/kernel.elf` ，与我们的应用源码无关

- 可能需要一些虚拟网络设备（事先配置好的tap或bridge）

- 启动参数（包括要运行的命令）

以上内容是针对原始的Firecracker程序而言，OSv仓库提供的firecracker.py和其它脚本方便了这个过程，但只能启动一台使用网络的VM，我之后会进行升级以满足我们启动多示例的需求