===================================
Welcome to edoping's documentation!
===================================

主要功能
--------

* 流程化带电点缺陷的形成能计算
* 完全基于命令行，无需编程和复杂的脚本
* 可以进行多组元体系的元素化学势估计
* 基于 OQMD 的竞争相结构和形成能获取
* 缺陷形成能的修正项计算
* 自洽费米能级的估计

程序安装
--------

edoping 程序包基于 python3 软件，确保它已经被正确安装。
程序包从 Github 下载，或者利用 git :

.. code-block:: bash

   $ git clone XXXXXXXXXXXXXXXXXX

对于中国大陆地区，也可以从 Gitee 获取源码，与上面类似：

.. code-block:: bash

   $ git clone XXXXXXXXXXXXXXXXXX

下载源码后，进入文件夹 (如果是压缩文件需要先解压缩) ，确保网络通畅,
我们可以通过 ``pip`` (或 ``pip3``) 工具来自动安装程序以及所有依赖的库
(实际上只依赖于 numpy 和 sicpy):

.. code-block:: bash

   $ pip install .

安装完成，我们就可以通过 ``edp`` 命令来使用 edoping 程序包了。
通过 ``-h`` (或者 ``--help``) 选项可以打印帮助信息，
同时检查安装是否成功：

.. code-block::

   $ edp -h
   usage: edoping [-h] [-v] [-q] Subcommand ...

   defect calculation - v0.1.4

   optional arguments:
     -h, --help       show this help message and exit
     -v, --verbosity  increase output verbosity
     -q, --quiet      only show key output

   Tips:
     Subcommand       Description
       cal            Calculate defect fromation energy
       energy         Read final energy from OUTCAR
       ewald          Read Ewald from OUTCAR
       volume         Read volume from OUTCAR
       epsilon        Read epsilon from OUTCAR
       evbm           Read VBM from EIGENVAL
       boxhyd         Place a single hydrogen atom in the box
       move           Move atomic position in cell
       replace        Replace atoms X by Y
       groupby        Group atoms by radial distribution function
       diff           Show difference between two POSCAR
       query          Fetch data from OQMD website
       chempot        Calculate chemical potential
       trlevel        Calculate transition levels
       scfermi        Calculate sc-fermi level
       fzfermi        Calculate fz-fermi level

   >>>>>>>>>> Citation of EDOPING <<<<<<<<<<
   If you have used EDOPING, please cite the following article:
   Jingyu Li, Jianbo Zhu, Yongsheng Zhang, et al, ..., 2023
   DOI:XXXXXX/XXXX/XXXX-XXXX

我们可以进一步查看子命令的帮助信息:

.. code-block:: 

   $ edp replace -h
   usage: edoping replace [-h] [-i FILENAME] [-o FILENAME] X Y

   positional arguments:
     X                     Name of previous atom
     Y                     Name of present atom

   optional arguments:
     -h, --help            show this help message and exit
     -i FILENAME, --input FILENAME
                           Input filename(default: POSCAR)
     -o FILENAME, --output FILENAME
                           Output filename(default: POSCAR)

点缺陷形成能计算
----------------

在第一性原理的计算框架下，这里所有的计算都围绕能量 (或者也被称为焓值) 计算进行。
对于一个带电量为 :math:`q` 的缺陷 :math:`D` ，其形成能定义为：

.. math:: 

   \Delta H _{D} ^{q} (E _{F}) = E _{D} ^{q} - E _{perfect} + \sum _{i} {n _{i} \mu _{i}} + q E _{F} + E _{corr}

这里，:math:`E_D^q` 表示带电量为 :math:`q` 的缺陷 :math:`D` 的超胞的能量，
:math:`E_{perfect}` 表示对应的完美超胞的能量，
:math:`\mu_i` 表示形成缺陷过程中失去
() 或者加入
() 的原子的化学势，
:math:`n_i` 为对应的原子数量，
:math:`E_F` 是实际缺陷体系的费米能级，
:math:`E_{corr}` 是一些能量修正项，
比如来自于周期边界条件的影响、静电势的变化等等。
通常情况下，我们不能够准确定位体系费米能级的位置，
但是能够知道它位于带隙附近。因此，我们通常是给出
:math:`\Delta H_D^q` - :math:`E_F` 关系曲线，
因此这里我们将形成能表示为费米能级的函数。
接下来，我们将逐步解释其它每一项的计算，以及最终的数据处理过程。

缺陷晶胞构建与体系能量计算
^^^^^^^^^^^^^^^^^^^^^^^^^^

完美晶胞的能量比较容易获得，因此我们这里将从缺陷结构的能量计算谈起。
我们首先考虑单一点缺陷的晶胞结构构建，包括空位、置换和间隙。
对于空位和间隙缺陷，通常我们可以直接手动修改 POSCAR 文件
获得缺陷结构，由于这个过程中我们不需要改变原子位置列表顺序。
对于取代缺陷，可以利用 :option:`replace` 从 POSCAR 文件来构建结构。
也可以借助一些晶体学可视化工具来辅助我们产生缺陷结构，
比如免费的 VESTA 软件。

当我们需要考虑更加复杂的缺陷时，可能的超胞结构构型数量将急剧增长，
利用结构的对称性我们能够有效减小所需的计算量。
对于比较简单的情况，我们可以利用结构可视化程序进行观察分析，
排除对称等价的结构，但是对于复杂的结构我们就很难处理了。
另外，专门处理这方面问题的软件和程序也非常有限。
在我们的软件中，集成了一个 :option:`groupby` 命令，
可以用来辅助我们筛选出不等价的结构。
当我们需要在一个已包含缺陷的结构上需要再引入一个缺陷时，
我们舍弃了从传统的对称性来考虑等价性，
而是从近邻的环境进行分析，将具有相似环境的原子归为一组，
从而找出具有代表性的结构。由于点缺陷的局域特性，
近邻分析可能是一种更加直接有效的方式来确定候选复合缺陷构型的方式。

当缺陷结构构造好后，
我们可以通过 :option:`diff` 命令来对比原始的晶胞和当前晶胞的差异，
确保我们构造的构型是我们想要的。

.. seealso::

   * :option:`replace` - 产生原子取代结构
   * :option:`groupby` - 不等价原子位置分析
   * :option:`diff` - 晶体结构对比与分析

当缺陷结构构建好后，我们将需要花费一定的时间来驰豫晶胞的结构，
从而获得收敛的能量值。而且，我们需要改变每种缺陷结构体系的电子数目，
来模拟不同的带电情况，得到相应的能量值
(具体操作可以参考[XXXXXXXXX])。

对于 VASP 软件，如果结构优化/自洽计算正常结束，
我们可以通过 ``grep`` 命令配合 ``tail`` 命令从 OUTCAR 读取能量:

.. code-block::

   $ grep 'energy  without entropy' OUTCAR | tail -n 1
     energy  without entropy=     -755.64631647  energy(sigma->0) =     -755.65114440

这个例子中，体系的能量值为 -755.646 eV。

.. seealso::

   * :option:`energy` - 从 OUTCAR 读取体系能量值。

化学势计算与数据库使用
^^^^^^^^^^^^^^^^^^^^^^

在我们完成缺陷结构的构建和相关的计算后，
应该可以注意到一个重要的事情：
缺陷结构和相应的完美结构很难保持原子数目的守恒。
为了评估缺陷的形成能，我们就必须要消除原子本身的能量的差异，
也就是我们这里所说的化学势。
一个直接的想法是，我们可以用相应的单质材料计算来评估单个原子的能量。
然而事实却是，这是一种非常粗糙的评估，伴随有严重的系统误差。
我们可以想象，我们目标化合物中原子的能量，一定是低于单质中原子的能量，
否则我们的目标化合物将会分解成单质来降低系统的能量。
这里，一般将化合物中原子的能量称为化学势 :math:`\mu_i`,
将单质中原子的能量称为标准化学势 :math:`\mu _i^\Theta`,
然后有 :math:`\mu_i = \mu _i^\Theta + \Delta \mu _i`,
这里我们的目标就是确定 :math:`\Delta \mu _i` 的大小。
遗憾的是，目前没有办法来给出一个确切的 :math:`\Delta \mu _i` 值，
我们能作的就是进行范围估计，
然后根据具体的实验环境进一步确定其值的大小。

按照我们前面的讨论，我们可以明确的知道一定有

.. math:: 

   \Delta \mu _i < 0

另外一方面，按照能量守恒，
我们知道化合物中所有元素的内能改变量就是该化合物的形成焓
:math:`\Delta H _{comp}`
也就是

.. math:: 

   \sum _i {c_i \cdot \Delta \mu _i} = \Delta H _{comp}

这里，假设 :math:`c_1 + c_2 + \ldots + c_N = 1`，
而且 :math:`\Delta H _{comp}` 为平均每个原子的形成焓。
我们由此可以确定 :math:`\Delta \mu _i` 的下边界：

.. math:: 

   c_i \cdot \Delta \mu _i > \Delta H _{comp}

在实验中，称 :math:`\Delta \mu _i = 0` 时的 :math:`\mu _i` 
为 "rich", 称 :math:`\Delta \mu _i = \Delta H _{comp} / c _i`
时的 :math:`\mu _i` 为 "poor"。

对于二元化合物，我们不难注意到，当一种元子的化学势为 "rich" 时，
另外一种原子的化学势必然为 "poor"。
因此，我们通常会给出两种原子分别为 "rich" 的情况来计算缺陷形成能，
反映了化学环境从一个极端到另外一个极端的情况，
真实的实验情况必然介于这两个极限情况之间。

随着元素种类增加到三种时, "poor" 和 "rich" 的概念就比较复杂了，
因为当一种原子为 "rich" 时，另外两种原子的情况我们并不能确定，
我们不得不进行细致的分类讨论，从而尽可能的接近实验环境。

尽管如此，这个范围依然太粗糙了。
目前，最有效的进一步缩小化学势范围的办法就是考虑加入竞争相的考虑。
按照我们前面的分析不难想到，
目标化合物中各原子的化学势之和必然小于竞争性的形成焓，
否则实验中就应该是形成更 “稳定” 的竞争相而不我们的目标相。
由此我们可以引入一系列的不等式约束:

.. math:: 

   \sum _i {c _{j,i} \cdot \Delta \mu _{j,i}} \leq \Delta H _{comp,j}

这里的角标 :math:`j` 表示第 :math:`j` 竞争相。
在这一系列的不等式约束下，化学势的范围会更加精细，
可行域的形状也变得更加复杂。

在我们的程序设计中，摈弃了对可行域形状的讨论，
而是将注意力直接放在了每种元素的化学势取值范围上。
尤其对于多组元化合物，当元素种类为 N 时，
其可行域的维度为 N-1 ，由于第二相对可行域的裁剪，
使其形状变得及其复杂。
此时我们没有精力去关注所有顶角的情况，
而且希望直接地知道某种关心元素的化学势范围。
我们的程序正是为此开发了 :option:`chempot` 命令，
来直接地获取不同元素的化学势取值范围。

手动处理大量竞争相是一个费力耗时的过程，
因此我们提供了 :option:`query` 命令来，
能够从数据库直接获取所有竞争相结构文件。
同时，我们还可以从数据库同时拉取竞争相的形成焓,
方便我们检查自己的计算结果。
另外一方面，在第一性原理的计算框架下，
体系的能量值是依赖于赝势和计算程序的，
但是物质的形成焓具有较好的稳定性。
当我们对精度的要求不高时，或者进行初步试探时，
我们完全可以利用数据库的竞争相形成焓来确定元素化学势的范围，
加速我们的工作进程。

.. seealso:: 

   * :option:`chempot` - 根据化合物和竞争相形成焓估计原子的化学势
   * :option:`query` - 从数据库获取竞争相结构和形成焓

.. warning:: 

   由于数据库的高通量计算缘故，形成焓精度非常有限，
   因此只建议作为初步探索使用，
   我们无法对数据库获取到的数据可靠性作任何保证。
   此外，此功能的开发主要是为了方便大家交流学习，
   如有任何侵权行为，我们会立即关停此功能。

缺陷形成能的修正项
^^^^^^^^^^^^^^^^^^

点缺陷形成能计算结果处理
^^^^^^^^^^^^^^^^^^^^^^^^

附录
----

命令行使用参考
^^^^^^^^^^^^^^
   
我们可以通过 ``edp -h`` 来查看所有支持的命令，
一般命令的使用格式为：

.. code-block:: bash

   $ edp [-v| -q] <command> --option1 --option2 [inputfile]

这里的 ``-v`` 选项可以增加屏幕的显示信息，
而 ``-q`` 选项会尽量抑制屏幕的显示信息。
我们可以通过子命令的 ``-h`` 选项来查看支撑的操作，
比如查看 ``chempot`` 命令支持的选项：

.. code-block:: bash

   $ edp chempot -h

接下来我们将介绍支持的子命令 (以字母表顺序排序):

.. option:: chempot

   求解元素化学势的范围

   这里我们需要准备一个输入文件 (默认文件名为 EDOPING.cmpot),
   第一行需要以 '#' 号开始, 然后依次是每种元素的名称，
   以空格分隔。接下来是所有考虑的化合物的元素配比，
   以及相应的能量值。
   这里，第一个出现的化合物 (也就是文件的第二行) 
   会被程序认定为目标化合物，也就是我们的基体相物质。

   **重要提醒**: 在处理元素配比和能量时，
   由于个人习惯以及不同数据库的格式规范差异，
   我们需要非常小心这里的归一化相关的问题:
   
   * 元素配比格式: (1) 晶胞中每种原子数目 (2) 最简原子数比 (3) 归一化比例
   * 化合物的焓值表示: (A) 晶胞的总焓值 (B) 平均每个原子的焓值
   * 焓值的参考: (I) 绝对焓值，即计算程序中给出的焓值 
     (II) 形成焓，即相对与对应单质的焓值差
   
   在程序内部，我们实际上是在处理类似下面的式子:

   .. math:: 

      \frac{1}{C} \sum _{i} {c _{i} \cdot \mu _{i}} \le \mu
   
   这里，:math:`i` 代指不同的化合物，
   :math:`c_i` 是输入文件的元素配比，
   :math:`\mu` 是输入文件的化合物焓值；
   如果使用了 ``-n`` (``--norm``) 选项，则
   :math:`C = \sum _i c_i`，否则 :math:`C=1`。
   简单来说，为了得到正确的结果，
   对于 (1+B) 和 (2+B) 情况需要指定 ``-n`` (``--norm``) 选项，
   而对于 (1+A) 和 (3+B) 情况则需要避免该选项。
   由于缺少必要的信息，我们无法处理 (2+A) 和 (3+A) 的情况，
   需要使用者进行必要的数据处理。

   至于焓值的参考问题，基本原则就是：
   最终求解化学势的参考就是初始给定化合物焓值的参考。
   如果提供的都是 (I) 绝对的焓值，那么给出的就是绝对化学势；
   如果提供的都是 (II) 形成焓，那么给出的元素化学势和对应单质的差值。

.. option:: diff

   结构对比

.. option:: energy

   从 OUTCAR 文件读取最后一步的能量。

.. option:: groupby

   元素分组

.. option:: query

   从材料数据库 (目前只支持 `OQMD <https://www.oqmd.org>`_) 获取竞争相的信息

   使用时确保网络畅通，且受制于数据库的访问频率限制，
   不建议在短时间内反复多次使用。
   通常情况下，可以先到数据库官网进行查询，
   具有更好的可视化结果，然后再通过该命令进行数据获取。
   
   通过该命令我们可以得到用于化学势估计的输入数据文件 EDOPING.cmpot,
   其中给定的最简原子比和化合物平均每个原子的形成焓。因此，
   为了得到正确的化学势 :math:`\Delta \mu_i`，
   在使用 ``edp`` :option:`chempot` 进行计算时需要添加
   ``-n`` (``--norm``) 选项。

.. option:: replace

   缺陷构建

输入/输出文件格式
^^^^^^^^^^^^^^^^^

缺陷形成能修正
^^^^^^^^^^^^^^

计算细节讨论
^^^^^^^^^^^^

调整体系的电荷
""""""""""""""

介电常数的计算
""""""""""""""

马德隆常数
""""""""""

XXXXXXXXXXXXXXXXXX

文章引用
--------

**如果此软件以及文档给您的工作提供了帮助，
请引用我们的文章让更多人知道，这对我们很重要，非常感谢！**

XXXXXXXXXXXXXXXXXXXXXXXXX

**参考文献**

XXXXXXXXXXXXXXXX
