import sys


__all__ = ['filein', 'fileout', 'filedata', 'filetrans', 'filedebug',
           '__prog__', '__author__', '__version__', '__date__', '__description__',
           '__changelog__', '__info__', '__link__', '__ref__',
           'required', 'Logger']


filein = 'PYDEFECT.in'
fileout = 'PYDEFECT.log'
filedata = 'PYDEFECT.dat'
filetrans = 'PYDEFECT.trans'
filedebug = 'PYDEFECT.debug'

__prog__ = 'PYDEFECT'
__author__ = 'Jianbo ZHU'
__version__ = '1.4'
__date__ = '2022-03-16'
__description__ = 'defect calculation'
__changelog__ = """
    1.0     first version
    1.1     add debug module
    1.2     improved screen output information
            redirct stdout to both file and console
    1.3     enable move atom in unit and write poscar
    1.4     self-consistent Fermi level
            equilibrium concentration
            *effective charge
"""

__info__ = """
Created on Wed Oct 20 12:52:06 2021

@author: Jianbo Zhu
@date: 2021/10/23
"""

__link__ = """
GitHub for new relase
"""

__ref__ = """
Jingyu Li, Yongsheng Zhang, et al, ..., 2022
DOI:XXXXXX/XXXX/XXXX-XXXX
"""


def required(is_import, pname='required package'):
    def dectorate(func):
        return func
    if is_import:
        return dectorate
    else:
        raise ImportError('Failed to import {}'.format(pname))


class Logger():
    def __init__(self, filename=fileout):
        self.terminal = sys.stdout
        self.log = open(filename, "w")
   
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        pass 
    
    def stop(self):
        sys.stdout = sys.__stdout__
        self.log.close()
