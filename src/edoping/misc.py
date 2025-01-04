from functools import wraps
import sys


__all__ = ['filein', 'fileout', 'filedata', 'filetrans', 'filecmpot', 'filedebug',
           '__prog__', '__author__', '__version__', '__date__', '__description__',
           '__ref__', 'required', 'Logger']

__prog__ = 'EDOPING'

filein = '{}.in'.format(__prog__)
fileout = '{}.log'.format(__prog__)
filedata = '{}.dat'.format(__prog__)
filetrans = '{}.trans'.format(__prog__)
filecmpot = '{}.cmpot'.format(__prog__)
filedebug = '{}.debug'.format(__prog__)


__author__ = 'Jianbo ZHU, Jingyu LI, Yongsheng ZHANG, et al.'
__version__ = '0.1.5'
__date__ = '2025-01-04'
__description__ = 'Point Defect Formation Energy Calculation'

__ref__ = """
Jianbo Zhu, Jingyu Li, Yongsheng Zhang, et al, ..., 2025
DOI:XXXXXX/XXXX/XXXX-XXXX
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
