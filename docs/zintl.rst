================
eDoping 学习分享
================

**作者：** 郭沐春 (西华大学, gmc@mail.xhu.edu.cn)

以 1-2-2 型 Zintl 相材料 YbMg\ :sub:`2`\ Sb\ :sub:`2` （晶体结构参考 Materials Project 
数据库的 `mp-2646 <https://next-gen.materialsproject.org/materials/mp-2646>`_ ）
中 Mg 被掺杂原子 Zn 取代的缺陷形成能计算为例，介绍 eDoping 程序的使用方法。
这里进行 2x2x2 的扩胞得到 Yb\ :sub:`8`\ Mg\ :sub:`16`\ Sb\ :sub:`16` ，
将其中任意一个 Mg 用 Zn 取代得到 Yb\ :sub:`8`\ Mg\ :sub:`15`\ ZnSb\ :sub:`16` 。

1. 创建文件夹
-------------

新建一个自己命名的文件夹，我记为 YbMg2Sb2, 在该文件夹中继续进行文件夹的构建：

.. code-block:: bash

    $ mkdir 1.perfect 2-1.Zn-Mg 3.phases 4-1.corr-dielectric 4-2.corr-hydrogen 

2. 完美晶胞自洽计算
-------------------

将结构优化后的超胞 Yb8Mg16Sb16-POSCAR 文件导入1.perfect 文件夹后，进行一步自洽计算。

3. 计算各种带电量缺陷结构的能量
-------------------------------

(1) 进入 2-1.Zn-Mg 这个文件夹，并在内新建一个relax文件夹：

.. code-block:: bash

    $ mkdir relax

进入该 relax 文件夹，将完美 Yb\ :sub:`8`\ Mg\ :sub:`16`\ Sb\ :sub:`16` 的 POSCAR
文件拷过来，用下面的命令构建出 Zn 占 Mg 的 POSCAR 缺陷结构文件：

.. code-block:: bash

    $ edp replace -o POSCAR-sub Mg Zn

这里 POSCAR-sub 就是 Zn 占 Mg 的缺陷结构文件
（Yb\ :sub:`8`\ Mg\ :sub:`15`\ ZnSb\ :sub:`16`），
对其进行结构优化。

(2) 返回到 2-1.Zn-Mg 文件夹的目录下，创建并进入文件夹 charge_0：

.. code-block:: bash

    $ mkdir charge_0
    $ cd charge_0

将前面 relax 中进行结构优化后的 CONTCAR 文件拷过来作为 POSCAR：

.. code-block:: bash

    $ cp ../relax/CONTCAR POSCAR

准备好自洽计算的 KPOINTS、POTCAR、INCAR 文件，然后回到 2-1.Zn-Mg 
文件夹的目录下，运行：

.. code-block:: bash

    $ cd ..
    $ edp fixchg -i charge_0 -3 -2 -1 1 2 3

就能够根据 charge_0 得到一系列不同带电配置的文件夹，每一个文件夹里面均有
INCAR、POSCAR、POTCAR 和 KPOITNS 文件。此时在 2-1.Zn-Mg 
文件夹下运行 ``ls`` 命令应该能够查看到如下内容：

.. code-block:: bash

    $ ls
    charge_+1  charge_+2  charge_+3  charge_-1  charge_-2  charge_-3  charge_0

(3) 将 7 个 charge_XX 文件夹提交进行自洽计算。

4. 找出竞争相
-------------

进入 3.phases 文件中。

(1) 计算单质原子的能量。由于我的体系中涉及的原子为 Yb、Mg、Sb 和 Zn，
所以我需要在数据库中分别找到这四种元素单质的 POSCAR 文件进行结构优化，
得到系统能量，再除以原子个数得到平均每个原子的能量。
通过下面的命令可以自动计算系统中每个原子的平均能量：

.. code-block:: bash

    $ edp energy --ave

该能量值也是该元素的标准化学势 :math:`\mu _i^\Theta` ，也就是化学势
:math:`\mu_i = \mu _i^\Theta + \Delta \mu _i` 式子中的第一项。 

(2) 计算 :math:`\Delta \mu _i` 。在 3.phases 目录下创建新的文件夹
YbMg2Sb2-Zn 并进入该文件夹：

.. code-block:: bash

    $ mkdir YbMg2Sb2-Zn
    $ cd YbMg2Sb2-Zn

通过下面的命令自动下载所有与 YbMg2Sb2 和 Zn 相关竞争相的信息：

.. code-block:: bash

    $ edp -v query YbMg2Sb2 -s -e 0.02 -x Zn

该命令不仅会获得所有竞争相的 POSCAR ，还会自动生成一个名为 EDOPING.cmpot 的文件，
其中包含了所有竞争相的形成能。然后执行命令：

.. code-block:: bash
    :emphasize-lines: 5,6

    $ edp chempot -n
    status  condition    miu(Yb)   miu(Mg)   miu(Sb)   miu(Zn)
       0    Yb-rich      -0.8242    0.0000   -1.3983   -0.2264
       0    Yb-poor      -2.3589   -0.6310   -0.0000   -0.1262
       0    Mg-rich      -0.8242    0.0000   -1.3983   -0.2264
       0    Mg-poor      -1.7342   -0.8355   -0.1079   -0.6175
       0    Sb-rich      -2.3589   -0.6310   -0.0000   -0.1262
       0    Sb-poor      -0.8242    0.0000   -1.3983   -0.2264

根据自己想要的环境得到 :math:`\Delta \mu _i` 。

5. 计算介电常数
---------------

进入 4-1.corr-dielectric 文件夹，将结构优化好的完美晶胞 POSCAR 文件
（超胞和原胞都可以）复制过来，利用下面的 INCAR 计算介电常数：

.. code-block::

    Global Parameters
    ISTART =  0            (Read existing wavefunction; if there)
    ISPIN  =  1            (Non-Spin polarised DFT)
    LREAL  = .FALSE.       (Projection operators: automatic)
    ENCUT  =  500          (Cut-off energy for plane wave basis set, in eV)
    PREC   =  Accurate     (Precision level)
    LWAVE  = .FALSE.       (Write WAVECAR or not)
    LCHARG = .FALSE.       (Write CHGCAR or not)

    Static Calculation
    NSW    = 1
    IBRION =  8
    ISMEAR =  0            (gaussian smearing method)
    SIGMA  =  0.01         (please check the width of the smearing)
    NELM   =  60           (Max electronic SCF steps)
    EDIFF  =  1E-08        (SCF energy convergence; in eV)
 
    Macroscopic Dielectric Tensor
    LEPSILON = .TRUE.
    LPEAD = .TRUE.

提交计算任务。计算结束后，转到主目录 YbMg2Sb2 下，执行：

.. code-block:: bash

    $ edp epsilon -f 4-1.corr-dielectric/OUTCAR
    HEAD OF MICROSCOPIC STATIC DIELECTRIC TENSOR (INDEPENDENT PARTICLE, excluding Hartree and local field effects)
    ------------------------------------------------------
    25.438394     0.000000    -0.000000
    0.000000    25.438394     0.000000
    -0.000000    -0.000000    25.438394
    ------------------------------------------------------

    MACROSCOPIC STATIC DIELECTRIC TENSOR (including local field effects in DFT)
    ------------------------------------------------------
    24.482055     0.000000    -0.000000
    0.000000    24.482055    -0.000000
    -0.000000     0.000000    24.482055
    ------------------------------------------------------

    MACROSCOPIC STATIC DIELECTRIC TENSOR (including local field effects in DFT)
    ------------------------------------------------------
    24.482055     0.000000    -0.000000
    0.000000    24.482055    -0.000000
    -0.000000     0.000000    24.482055
    ------------------------------------------------------

    MACROSCOPIC STATIC DIELECTRIC TENSOR IONIC CONTRIBUTION
    ------------------------------------------------------
    19.549608    -0.000000    -0.000000
    -0.000000    19.549608     0.000000
    -0.000000     0.000000    19.549608
    ------------------------------------------------------

这里展示的是官方例子中的结果，实际计算结果可能有所不同。
具体需要关注的数值为最后一个张量和倒数第二个张量，
分别表示离子贡献的介电常数（19.55）和电子贡献的介电常数（43.93）。
对于具有各项异性的材料，可以简单对张量的对角线元素取平均值。

6. 计算马德龙常数
-----------------

这一步通过计含单氢原子同尺寸超胞的能量获得。进入 4-2.corr-hydrogen
文件夹里面，将 Yb\ :sub:`8`\ Mg\ :sub:`16`\ Sb\ :sub:`16` 
超胞结构优化后的 POSCAR 文件导入文件夹里面，然后执行：

.. code-block:: bash

    $ edp boxhyd

得到 POSCAR.H 文件。将其改名为 POSCAR，进行自洽计算，得到 OUTCAR 文件。
返回到主目录 YbMg2Sb2 下，执行：

.. code-block:: bash

    $ edp ewald -f 4-2.corr-hydrogen/OUTCAR
    Final (absolute) Ewald: 1.7152

得到的结果就是马德龙常数。

7. 计算形成能
-------------

(1) 在主目录 YbMg2Sb2 下，创建 EDOPING.in 文件：


.. code-block::
    :emphasize-lines: 1,2,3,11,12

    DPERFECT = 1.perfect
    DDEFECT  = 2-1.Zn-Mg
    CMPOT    = 0 -9.0147
    VALENCE  = -3 -2 -1 0 1 2 3
    # PREFIX   = charge_
    # DDNAME   = auto
    EVBM     = inf
    ECBM     = inf
    PENERGY  = inf
    PVOLUME  = inf
    EWALD    = 1.7152
    EPSILON  = 44.03
    BFTYPE   = 2
    EMIN     = -1
    EMAX     = 2
    NPTS     = 3001

**注意：** 上述 EDOPING.in 文件中高亮显示的需要检查，并且按照想要的化学环境
（比如 Mg-rich 或 Mg-poor）进行修改。 其中 “CMPOT    = 0 -9.0147” 
这个代表缺陷中得失原子的化学势，并且按照 “失去 得到 失去 得到 ...” 顺序成对出现。
对于 Yb\ :sub:`8`\ Mg\ :sub:`16`\ Sb\ :sub:`16` 变为
Yb\ :sub:`8`\ Mg\ :sub:`15`\ ZnSb\ :sub:`16` 中 Zn 占 Mg 的缺陷，
是指失去一个 Mg，得到一个 Zn，所以第一个化学势是 Mg，第二个化学势是 Zn，即
“CMPOT = :math:`\mu`\ :sub:`Mg` :math:`\mu`\ :sub:`Zn` ”。而 EDOPING.in 中
“EWALD = 1.7152” 为马德龙常数，“EPSILON = 44.03” 为介电常数。

(2) 准备好 EDOPING.in 文件后，在主目录 YbMg2Sb2 下，执行命令：

.. code-block:: bash

    $ edp cal -i EDOPING.in

运行结束后，会生成 EDOPING.log 和 EDOING.dat 文件， 分别记录了程序的运行日志和计算结果。
EDOING.dat 文件如下（这里仍然采用了官方手册中的示例数据，实际操作类似），
用第一列和第二列做图即可，第一列费米能级，第二列就是缺陷形成能。

.. code-block::

    # Ef, Eformation, q , q_-3, q_-2, q_-1, q_+0, q_+1, q_+2, q_+3;    1689.3500    1
    -1.0000 -1.6816 3.0000 5.8115 4.3378 2.8985 1.4866 0.0987 -0.8285 -1.6816
    -0.9990 -1.6786 3.0000 5.8085 4.3358 2.8975 1.4866 0.0997 -0.8265 -1.6786
    -0.9980 -1.6756 3.0000 5.8055 4.3338 2.8965 1.4866 0.1007 -0.8245 -1.6756
    -0.9970 -1.6726 3.0000 5.8025 4.3318 2.8955 1.4866 0.1017 -0.8225 -1.6726
    -0.9960 -1.6696 3.0000 5.7995 4.3298 2.8945 1.4866 0.1027 -0.8205 -1.6696
    -0.9950 -1.6666 3.0000 5.7965 4.3278 2.8935 1.4866 0.1037 -0.8185 -1.6666
    -0.9940 -1.6636 3.0000 5.7935 4.3258 2.8925 1.4866 0.1047 -0.8165 -1.6636
    -0.9930 -1.6606 3.0000 5.7905 4.3238 2.8915 1.4866 0.1057 -0.8145 -1.6606
    -0.9920 -1.6576 3.0000 5.7875 4.3218 2.8905 1.4866 0.1067 -0.8125 -1.6576
    ...

8. 空位和间隙原子结构的构建
---------------------------

(1) Yb\ :sub:`8`\ Mg\ :sub:`16`\ Sb\ :sub:`16` 中 Zn 占 Mg 位的构建，
通过执行下面的命令获得 Yb\ :sub:`8`\ Mg\ :sub:`15`\ ZnSb\ :sub:`16` ：

.. code-block:: bash

    $ edp replace -o POSCAR-sub Mg Zn

(2) Yb\ :sub:`8`\ Mg\ :sub:`16`\ Sb\ :sub:`16` 中 Yb 空位的构建，
通过执行下面的命令获得 Yb\ :sub:`7`\ Mg\ :sub:`16`\ Sb\ :sub:`16` ：

.. code-block:: bash

    $ edp replace -o POSCAR-vac Yb Vac

(3) 间隙原子的构建，首先必须要知道自己体系内的间隙的位置在哪里（需要依赖第三方寻找间隙的程序），
通过执行下面的命令获得带有间隙原子的结构文件：

.. code-block:: bash

    $ edp replace -o POSCAR-int Vac Zn -p 0 0 0.25

其中 -p 后面的位置是指 Yb\ :sub:`8`\ Mg\ :sub:`16`\ Sb\ :sub:`16` 中间隙位置的分数坐标位置。
