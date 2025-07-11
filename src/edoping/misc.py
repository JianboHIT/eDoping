from functools import wraps
import sys


__prog__ = 'EDOPING'

filein = '{}.in'.format(__prog__)
fileout = '{}.log'.format(__prog__)
filedata = '{}.dat'.format(__prog__)
filetrans = '{}.trans'.format(__prog__)
filecmpot = '{}.cmpot'.format(__prog__)
filedebug = '{}.debug'.format(__prog__)


__author__ = 'Jianbo Zhu, Jingyu Li, Peng-Fei Liu'
__version__ = '0.3.0'
__date__ = '2025-07-11'
__description__ = 'Point Defect Formation Energy Calculation'

__ref__ = """
 J. Zhu, J. Li, P. Liu, et al, eDoping: A high-throughput software
 package for evaluating point defect doping limits in semiconductor
 and insulator materials, Materials Today Physics, 55 (2025) 101754.
 DOI: 10.1016/j.mtphys.2025.101754
"""


def required(is_import, pname='required package'):
    def dectorate(func):
        @wraps(func)
        def function(*args, **kwargs):
            if is_import:
                return func(*args, **kwargs)
            else:
                disp_info = 'Failed to import {}'.format(pname)
                raise ImportError(disp_info)
        return function
    return dectorate


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
