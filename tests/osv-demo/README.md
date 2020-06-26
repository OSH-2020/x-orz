# 试验记录

本机环境下使用node.js进行测试，工作正常。

使用本目录中的镜像与 /tools/firecracker.py 脚本进行测试，集群启动是正常的，其他部件也可以成功在 keyvaluestore 之中注册自身地址，但是在上传图片时，如果使用 osv-microservice-demo 项目下的 bin/upload_batch.sh 脚本进行测试，会反馈 Error uploading image：null 。（此脚本似乎是以keyvaluestore的地址作为参数，向它询问master地址？），如果直接向 master 上传图片（使用curl），则会直接导致 master 抛出异常，说明 files 为null。

对脚本运行过程进行strace，结果在error.txt下。