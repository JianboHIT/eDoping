import numpy as np
from io import StringIO
from collections.abc import Iterable

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
def pminmax(filename, objcoefs=None, referance=None, normalize=False):
    '''
    Calculate chemical potential under poor and rich conditions.

    Parameters
    ----------
    filename : str
        A file contains formation energy.
    objcoefs : float-list
        Customized coefficients of the linear objective function.
    referance : float-list, optional
        The referance values of chemical potential, by default None.
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
    if referance is None:
        refs = 0
    else:
        refs = np.asarray(referance)
        if A_eq.shape[-1] != refs.shape[-1]:
            raise RuntimeError('The number of referance values is not equal to species')

    # print(A_ub, b_ub, A_eq, b_eq, bounds, refs)
    
    Nelmt = A_eq.shape[-1]
    if objcoefs is None:
        names = []
        objcoefs = []
        for idx, (weights, label) in enumerate(zip(A_eq.T, labels)):
            if np.all(weights < 1E-4):
                continue

            # rich
            objcoef = np.zeros(Nelmt)
            objcoef[idx] = 1
            names.append('{}-rich'.format(label))
            objcoefs.append(objcoef)

            # poor
            objcoef = np.zeros(Nelmt)
            objcoef[idx] = -1
            names.append('{}-poor'.format(label))
            objcoefs.append(objcoef)
    else:
        if len(objcoefs) == Nelmt:
            names = ['  --', ]
            objcoefs = np.atleast_2d(objcoefs)
        else:
            raise RuntimeError('The number of objective coefficients is not equal to species')

    results= []
    for name, copt in zip(names, objcoefs):
        rst = linprog(-copt, A_ub, b_ub, A_eq, b_eq, bounds)
        result = (name, rst.x + refs, rst.status, rst.message)
        results.append(result)
    return results, labels
