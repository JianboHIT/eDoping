# eDoping

A high-throughput software package for evaluating point defects.

**Online Documentation**
- English: https://jianbohit.github.io/eDoping/en/
- 简体中文: https://jianbohit.github.io/eDoping/

## Installiation

The `eDoping` package is built on Python3, so please ensure that it is 
properly installed on your system. If the network is available, 
the most efficient way to install the eDoping package is via 
`pip` (or `pip3`):

```
pip install eDoping
```

If you do not have internet access or are interested in the source code,
You can download the source code from GitHub using the following command:

```
git clone https://github.com/JianboHIT/eDoping.git
```

For users in mainland China, the source code is also available on Gitee. 
You can clone it using a similar command:

```
git clone https://gitee.com/joulehit/eDoping.git
```

After downloading the source code, navigate to the folder (make sure to 
unzip it if you downloaded it as a zip file) and ensure your internet 
connection is stable. Then, you can use `pip` (or `pip3`) to automatically 
install the package along with its dependencies, which primarily include 
NumPy and SciPy:

```
pip install .
```

Once the installation is complete, you can start using the `eDoping` package 
with the edp command. To verify that the installation was successful, 
you can use the `-h` (or `--help`) option to display the help information:

```
edp -h
```

This will print out the help information for the `eDoping` package, including 
all available sub-commands.
