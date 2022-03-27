from misc import required, filecmpot
import numpy as np
from io import StringIO


try:
    from scipy.optimize import linprog
except:
    is_import_lnp = False
else:
    is_import_lnp = True


def read_cmpot(filename=filecmpot):
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
    Nelmt = coefs.shape[-1]
    if header is None:
        header = ['A{:02d}'.format(idx+1) for idx in range(Nelmt)]
    elif len(header) < Nelmt:
        raise RuntimeError('The number of element is less than the coefficients')
    else:
        header = header[:Nelmt]
    
    st_eq_idx = np.all(data, axis=-1)
    st_eq_coefs = coefs[st_eq_idx, :]
    st_eq_energy = energy[st_eq_idx, :]
    
    st_ub_idx = np.logical_not(st_eq_idx)
    st_ub_coefs = coefs[st_ub_idx, :]
    st_ub_energy = energy[st_ub_idx, :]
    
    return header, (st_ub_coefs, st_ub_energy, st_eq_coefs, st_eq_energy)


@required(is_import_lnp, 'scipy')
def pminmax(filename):
    '''
    

    Parameters
    ----------
    filename : str
        A file contains formation energy to calculate chemical potential .

    Returns
    -------
    results : tuple-list
        [(name, x0, status, msg),...]

    '''
    names, constraints = read_cmpot(filename)
    A_ub, b_ub, A_eq, b_eq = constraints
    bounds = (None, None)
    
    results= []
    for name, copt in zip(names, np.identity(A_eq.shape[-1])):
        rst = linprog(copt, A_ub, b_ub, A_eq, b_eq, bounds) # poor condition
        result = ('{}-poor'.format(name), rst.x, rst.status, rst.message)
        results.append(result)
        
        rst = linprog(-copt, A_ub, b_ub, A_eq, b_eq, bounds) # rich conditon
        result = ('{}-poor'.format(name), rst.x, rst.status, rst.message)
        results.append(result)
        
    return results
