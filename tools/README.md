- **firecracker.py** - 启动 OSv 虚拟机

  ```shell
  sudo ./firecracker.py <image> <id> -e <cmdline>
  ```

  其中需要指定 id 为 [2:254] 间的整数，用于分配 IP ，不同 VM 的 id 不能相同（现有脚本暂时不支持自动分配 IP ）


