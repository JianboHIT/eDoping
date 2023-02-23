import numpy as np
from io import StringIO
from collections import Iterable

try:
    from scipy.optimize import linprog
except:
    is_import_lnp = False
else:
    is_import_lnp = True

from .misc import required, filecmpot

def read_cmpot(filename=filecmpot, eq_idx=0, normalize=False):
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    if '#' in lines[0]:
        header = lines[0].strip().lstrip('#').split()
        del(lines[0])
    else:
        header = None
    
    data = np.loadtxt(StringIO(''.join(lines)))
    coefs = data[:,:-1]    # (n,Nelmt)
    energy = data[:,-1:]   # (n,1)
    if normalize:
        Natom = coefs.sum(axis=-1, keepdims=True)
        energy *= Natom    # equal to ceefs /= Natom
    Nelmt = coefs.shape[-1]
    if header is None:
        header = [chr(idx+65) for idx in range(Nelmt)]   # A, B, C, ...
        # header = ['A{:02d}'.format(idx+1) for idx in range(Nelmt)]
    elif len(header) < Nelmt:
        raise RuntimeError('The number of element is less than the coefficients')
    else:
        header = header[:Nelmt]
    
    # st_eq_idx = np.all(data, axis=-1)
    # st_eq_coefs = coefs[st_eq_idx, :]
    # st_eq_energy = energy[st_eq_idx, :]
    # 
    # st_ub_idx = np.logical_not(st_eq_idx)
    # st_ub_coefs = coefs[st_ub_idx, :]
    # st_ub_energy = energy[st_ub_idx, :]
    
    if not isinstance(eq_idx, Iterable):
        eq_idx = [eq_idx, ]
    
    st_eq_coefs  = []
    st_eq_energy = []
    st_ub_coefs  = []
    st_ub_energy = []
    for i, (c, e) in enumerate(zip(coefs, energy)):
        if i in eq_idx:
            st_eq_coefs.append(c)
            st_eq_energy.append(e)
        else:
            st_ub_coefs.append(c)
            st_ub_energy.append(e)

    st_eq_coefs  = np.vstack(st_eq_coefs)
    st_eq_energy = np.vstack(st_eq_energy) 
    st_ub_coefs  = np.vstack(st_ub_coefs)
    st_ub_energy = np.vstack(st_ub_energy)
    
    return header, (st_ub_coefs, st_ub_energy, st_eq_coefs, st_eq_energy)


@required(is_import_lnp, 'scipy')
def pminmax(filename, objcoefs=None, normalize=False):  
    '''
    Calculate chemical potential under poor and rich conditions.

    Parameters
    ----------
    filename : str
        A file contains formation energy.
    objcoefs : float-list
        Customized coefficients of the linear objective function.
    normalize : bool, optional
        Whether to normalize coefficients or not, by default False

    Returns
    -------
    results : tuple-list
        [(name, x0, status, msg),...], elmt_labels

    '''
    labels, constraints = read_cmpot(filename, normalize=normalize)
    A_ub, b_ub, A_eq, b_eq = constraints
    bounds = (None, None)
    # print(A_ub, b_ub, A_eq, b_eq, bounds)
    
    if objcoefs is None:
        names = labels
        objcoefs = np.identity(A_eq.shape[-1])
    else:
        if len(objcoefs) == A_ub.shape[-1]:
            names = ['Cond']
            objcoefs = [np.array(objcoefs),]
        else:
            raise RuntimeError('Encounter unmatched objective coefficients')
            
    results= []
    for name, copt in zip(names, objcoefs):
        rst = linprog(copt, A_ub, b_ub, A_eq, b_eq, bounds) # poor condition
        result = ('{}-poor'.format(name), rst.x, rst.status, rst.message)
        results.append(result)
        
        rst = linprog(-copt, A_ub, b_ub, A_eq, b_eq, bounds) # rich conditon
        result = ('{}-rich'.format(name), rst.x, rst.status, rst.message)
        results.append(result)
    return results, labels
