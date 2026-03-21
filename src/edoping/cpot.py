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


from itertools import combinations
from fractions import Fraction
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

def pyhull(Xcomp, Ecomp, ends=None):
    '''
    Computes the ground state convex hull and energies above the hull for a binary system.

    Parameters
    ----------
    Xcomp : 1D array_like
        Monotonically sorted phase compositions (e.g., mole fractions).
        Using `fractions.Fraction` is highly recommended to avoid floating-point
        artifacts when resolving degenerate tie-lines.
    Ecomp : 1D array_like
        Energies corresponding to `Xcomp`.
    ends : (int, int), optional
        Indices of the current tie-line endpoints. Evaluates the full composition
        range if None.

    Returns
    -------
    list of int
        Indices of the thermodynamically stable phases (hull vertices).
    numpy.ndarray or float
        Global E_above_hull for all phases. Returns `np.inf` for collapsed bounding boxes.
    '''
    Xcomp = np.asarray(Xcomp)
    Ecomp = np.asarray(Ecomp, dtype=float)

    if ends is None:
        end_a, end_b = 0, len(Xcomp) - 1
    else:
        end_a, end_b = ends

    Xa = Xcomp[end_a]
    Xb = Xcomp[end_b]

    if Xa >= Xb:
        return [], np.inf

    a = ((Xb - Xcomp) / (Xb - Xa)).astype(float)
    b = ((Xcomp - Xa) / (Xb - Xa)).astype(float)
    Ehull = Ecomp - a * Ecomp[end_a] - b * Ecomp[end_b]

    if np.all(Ehull >= 0):
        return [end_a, end_b], Ehull

    end_c = int(np.argmin(Ehull))
    convex_a, Ehull_a = pyhull(Xcomp, Ecomp, ends=(end_a, end_c))
    convex_b, Ehull_b = pyhull(Xcomp, Ecomp, ends=(end_c, end_b))
    return convex_a[:-1] + [end_c, ] + convex_b[1:], np.minimum(Ehull_a, Ehull_b)

def preact(coefs, energies, labels, ridx1=0, ridx2=1, with_hull=False):
    '''
    Evaluates chemical reactions between two reactants and determines their 
    thermodynamic stability via convex hull analysis.

    Parameters
    ----------
    coefs : array_like, int
        Composition matrix of shape (N_compounds, N_elements) representing the 
        stoichiometry of each phase. Must contain integer values.
    energies : array_like, float
        1D array of energies corresponding to each compound in `coefs`.
    labels : list of str
        List of elemental symbols corresponding to the columns in `coefs`.
    ridx1 : int, optional
        Index of the first reactant (0-based). Default is 0.
    ridx2 : int, optional
        Index of the second reactant (0-based). Default is 1.
    with_hull : bool, optional
        If True, computes the energy convex hull and E_above_hull for the generated
        reaction pathways. Default is False.

    Returns
    -------
    reaction_dict : dict
        A dictionary where keys are formatted reaction strings
        - `coeffs` (list of int): Integer stoichiometric coefficients.
        - `factor` (int): Scaling factor used to normalize to per-atom quantities.
        - `product_indices` (tuple of int): Indices of the product phases.
        - `delta_H_per_atom` (float): Reaction enthalpy normalized per atom.
        - `hull_energy` (float, optional): E_above_hull (only appended if `with_hull=True`).
    metadata : dict
        System metadata including tracking details such as the number of valid reactions, 
        elemental/compound counts, reduced empirical formula names, reactant properties, 
        and indices of the convex hull vertices.
    '''
    compounds = np.array(coefs, dtype=int, copy=True)
    enthalpies = np.array(energies, dtype=float, copy=True)

    if np.max(np.abs(compounds) - coefs) > 0.001:
        raise RuntimeError('The coefficients are not integer')
    Ncomp, Nelmt = compounds.shape

    # print("Reduced composition and energy (eV/cell):")
    comp_names = []
    for i in range(Ncomp):
        factor = np.gcd.reduce(compounds[i])
        compounds[i] //= factor
        enthalpies[i] /= factor
        comp_name = ''
        for e, r in zip(labels, compounds[i]):
            if r <= 0:
                continue
            elif r == 1:
                comp_name += e
            else:
                comp_name += '{}{}'.format(e, r)
        # print(i+1, " : ", factor, compounds[i], comp_name, "    ", enthalpies[i])
        comp_names.append(comp_name)
    # print()

    reaction_dict = dict()
    for product_combo in combinations(range(Ncomp), Nelmt-1):
        Aeq = np.transpose(compounds[[ridx1, ridx2, *product_combo]])
        Aeq[:, 2:] *= -1
        Aeq = np.vstack([Aeq, np.sum(Aeq, axis=0, where=(Aeq > 0))])
        Beq = np.zeros(Aeq.shape[0])
        Beq[-1] = 1

        Heq = enthalpies[[ridx1, ridx2, *product_combo]]
        Heq[:2] *= -1

        try:
            float_coeffs = np.linalg.solve(Aeq, Beq)
        except np.linalg.LinAlgError:
            continue

        float_coeffs[np.abs(float_coeffs) < 1e-8] = 0

        if np.any(float_coeffs < 0):
            continue

        # Calculate enthalpy per atom: delta_H = sum(coeffs · enthalpy_vector)
        delta_H_per_atom = np.dot(float_coeffs, Heq)

        # Convert coefficients to integers while maintaining the ratio
        factor = np.lcm.reduce([Fraction(x).limit_denominator().denominator for x in float_coeffs])
        int_coeffs = np.round(factor * float_coeffs).astype(int)

        reactants = []
        for i, r in zip([ridx1, ridx2], int_coeffs):
            if r <= 0:
                continue
            elif r == 1:
                reactants.append(comp_names[i])
            else:
                reactants.append('{} {}'.format(r, comp_names[i]))
        products = []
        for i, r in zip(product_combo, int_coeffs[2:]):
            if r <= 0:
                continue
            elif r == 1:
                products.append(comp_names[i])
            else:
                products.append('{} {}'.format(r, comp_names[i]))
        equat_str = "{} -> {}".format(" + ".join(reactants), " + ".join(products))
        reaction_dict[equat_str] = [int_coeffs, factor, product_combo, delta_H_per_atom]

    if with_hull:
        # Find hull vertices and energy above hull for all reactions
        combs = sorted([(Fraction(v[0][0], v[1]), k, v[3]) for k, v in reaction_dict.items()])
        Xcomp, Equat, Ecomp = list(zip(*combs))
        hull_vertices, hull_energy = pyhull(Xcomp, Ecomp)
        for k, h in zip(Equat, hull_energy):
            reaction_dict[k].append(h)
    else:
        hull_vertices = []

    metadata = {
        'Nreact': len(reaction_dict),
        'Nelmt': Nelmt,
        'Ncomp': Ncomp,
        'comp_names': comp_names,
        'reactant_1': dict(name=comp_names[ridx1], natom=np.sum(compounds[ridx1])),
        'reactant_2': dict(name=comp_names[ridx2], natom=np.sum(compounds[ridx2])),
        'hull_vertices': hull_vertices,
        'length_equ_str': max(len(k) for k in reaction_dict),
    }
    return reaction_dict, metadata
