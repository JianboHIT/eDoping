from functools import wraps
import sys


__all__ = ['filein', 'fileout', 'filedata', 'filetrans', 'filecmpot', 'filedebug',
           '__prog__', '__author__', '__version__', '__date__', '__description__',
           '__info__', '__link__', '__ref__',
           'required', 'Logger']

__prog__ = 'EDOPING'

filein = '{}.in'.format(__prog__)
fileout = '{}.log'.format(__prog__)
filedata = '{}.dat'.format(__prog__)
filetrans = '{}.trans'.format(__prog__)
filecmpot = '{}.cmpot'.format(__prog__)
filedebug = '{}.debug'.format(__prog__)


__author__ = 'Jianbo ZHU'
__version__ = '0.1.4'
__date__ = '2023-10-28'
__description__ = 'defect calculation'

__info__ = """
Created on Wed Oct 20 12:52:06 2021

@author: Jianbo Zhu
@date: 2021/10/23
"""

__link__ = """
GitHub for new relase
"""

__ref__ = """
Jingyu Li, Jianbo Zhu, Yongsheng Zhang, et al, ..., 2023
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
