#   Copyright 2023-2026, Jianbo Zhu, Jingyu Li, Peng-Fei Liu
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import numpy as np

try:
    from scipy.optimize import linprog
except:
    is_import_lnp = False
else:
    is_import_lnp = True

from .misc import required, filecmpot

def read_cmpot(filename=filecmpot, normalize=False):
    with open(filename, 'r') as f:
        # Only read the first line
        line = f.readline()

    if line.strip().startswith('#'):
        header = line.strip().lstrip('#').split()
    else:
        header = None

    full_data = np.loadtxt(filename)
    coefs = full_data[:,:-1]    # (n,Nelmt)
    energies = full_data[:,-1]    # (n,)
    if normalize:
        Natom = coefs.sum(axis=-1)
        energies *= Natom         # equal to ceefs /= Natom
    Nelmt = coefs.shape[-1]
    if header is None:
        labels = [chr(idx+65) for idx in range(Nelmt)]   # A, B, C, ...
        # header = ['A{:02d}'.format(idx+1) for idx in range(Nelmt)]
    elif len(header) < Nelmt:
        raise RuntimeError('The number of element is less than the coefficients')
    else:
        labels = header[:Nelmt]
    return coefs, energies, labels


@required(is_import_lnp, 'scipy')
def pminmax(coefs, energies, labels=None, objcoefs=None, referance=None, eq_idx=0):
    '''
    Calculate chemical potential under poor and rich conditions.

    Parameters
    ----------
    coefs: array-like
        The stoichometric coefficients of compounds.
    energies : array-like
        The formation energies of compounds.
    labels : list, optional
        The labels of components. It is useless if `objcoefs` is specified.
    objcoefs : float-list, optional
        Customized coefficients of the linear objective function.
    referance : float-list, optional
        The referance values of chemical potential, by default None.
    normalize : bool, optional
        Whether to normalize coefficients or not, by default False.
    eq_idx : int or list, optional
        The indices of equilibrium phases, by default 0.

    Returns
    -------
    results : tuple-list
        [(name, x0, status, msg),...]

    '''
    eq_idx = np.ravel(eq_idx)   # shape: (n_eq,)
    A_eq = coefs[eq_idx, :]
    b_eq = energies[eq_idx]
    A_ub = np.delete(coefs, eq_idx, axis=0)
    b_ub = np.delete(energies, eq_idx)
    bounds = (None, None)
    if referance is None:
        refs = 0
    else:
        refs = np.asarray(referance)
        if A_eq.shape[-1] != refs.shape[-1]:
            raise RuntimeError('The number of referance values is not equal to species')

    # print(A_ub, b_ub, A_eq, b_eq, bounds, refs, sep='\n\n')
    
    Nelmt = A_eq.shape[-1]
    if objcoefs is None:
        names = []
        objcoefs = []
        if not labels:
            raise RuntimeError('The labels of components are not given when objcoefs is None')
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
    return results
