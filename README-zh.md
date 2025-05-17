# eDpoing

带电点缺陷的高通量计算程序包。

软件手册：https://jianbohit.github.io/eDoping/

## 安装

`eDoping` 程序包基于 python3 软件，确保它已经被正确安装。
如果可以联网，最简单的方式就是通过 `pip` (或 `pip3`) 安装
eDoping 程序包:

```
pip install eDoping
```

如果无法联网或者对源代码感兴趣，可以从 Github 下载程序包，或者利用 git :

```
git clone https://github.com/JianboHIT/eDoping.git
```

对于中国大陆地区，也可以从 Gitee 获取源码，与上面类似：

```
git clone https://gitee.com/joulehit/eDoping.git
```

下载源码后，进入文件夹 (如果是压缩文件需要先解压缩) ，确保网络通畅,
我们可以通过 `pip` (或 `pip3`) 工具来自动安装程序以及所有依赖的库
(实际上只依赖于 numpy 和 sicpy):

```
pip install .
```

安装完成，我们就可以通过 `edp` 命令来使用 `eDoping` 程序包了。
通过 `-h` (或者 `--help`) 选项可以打印帮助信息，
检查安装是否成功:

```
edp -h
```

这会打印出 `eDoping` 程序包的帮助信息，包括所有可用的子命令。
