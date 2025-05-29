# eDoping

A high-throughput software package for evaluating point defects.

<div align="center"><img src="docs/_static/logo.png" width="360"></div><br>

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
with the `edp` command. To verify that the installation was successful, 
you can use the `-h` (or `--help`) option to display the help information:

```
edp -h
```

This will print out the help information for the `eDoping` package, including 
all available sub-commands.

## How to Cite

[1] J. Zhu, J. Li, Z. Ti, L. Wang, Y. Shen, L. Wei, X. Liu, X. Chen, P. Liu,
J. Sui, Y. Zhang, eDoping: A high-throughput software package for evaluating
point defect doping limits in semiconductor and insulator materials,
*Materials Today Physics*, 55 (2025) 101754,
https://doi.org/10.1016/j.mtphys.2025.101754.

[2] J. Li, J. Zhu, Z. Ti, W. Zhai, L. Wei, C. Zhang, P. Liu, Y. Zhang,
Synergistic defect engineering for improving n-type NbFeSb thermoelectric
performance through high-throughput computations,
*Journal of Materials Chemistry A*, 10 (46) (2022) 24598-24610,
https://doi.org/10.1039/d2ta07142h.
