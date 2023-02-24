import sys, os, time
import numpy as np
from collections import defaultdict
from .misc import Logger, filein, filetrans, filedata
from .misc import __prog__, __author__, __version__, __date__
from .dft import Cell, read_energy, read_volume, \
                 read_eigval, read_evbm, read_pot


__all__ = ['InputList', 'formation', 'read_formation', 'read_H0',
           'cal_trans', 'write_bsenergy', ]


class InputList():
    _default = {'dperfect': '../perfect',
                'ddefect': '.',
                'valence': [-2, -1, 0, 1, 2],
                'ddname': 'auto',
                'prefix': 'charge_',
                'evbm': float('inf'),
                'ecbm': float('inf'),
                'penergy': float('inf'),
                'pvolume': float('inf'),
                'ewald': 0,
                'epsilon': float('inf'),
                'bftype': 0,
                'cmpot': [0, 0],
                'emin': -1,
                'emax': 2,
                'npts': 1001}  # read-only
    __slots__ = _default.keys()

    def __init__(self, filename=None):
        for key in self.__slots__:
            setattr(self, key, None)  # inital to None
        if filename is not None:
            self.from_file(filename)

    def from_file(self, filename=filein):
        '''
        Update parameters from file manually.

        Parameters
        ----------
        filename : str, optional
            Filename of *.in file. The default is 'EDOPING.in'.

        '''
        with open(filename, 'r') as f:
            opts = self.parse(f.readlines())
        for opt in opts:
            setattr(self, opt[0], opt[1])

    def set_default(self):
        '''
        Auto-fill unset parameters.

        '''
        for key in self.__slots__:
            if getattr(self, key) is None:
                setattr(self, key, self._default[key])
        self.check()

    def check(self):
        '''
        Check input parameters. TODO
        
        '''
        if self.ddname == 'auto':
            prefix = self.prefix
            ddname = []
            for van in self.valence:
                if van == 0:
                    # {:+s} make 0(Int) to "+0"
                    ddname.append('{:s}0'.format(prefix))
                else:
                    ddname.append('{:s}{:+d}'.format(prefix, van))
            self.ddname = ddname
        dd = sorted(zip(self.valence, self.ddname), key=lambda x: x[0])
        self.valence, self.ddname = list(zip(*dd))  # sort by valence

    def __str__(self):
        '''
        Display in print().
        
        '''
        strs = ['{:>10s}: {}'.format(key.upper(), getattr(self, key))
                for key in self.__slots__]
        return '\n'.join(strs)

    @classmethod
    def parse(cls, lines):
        '''
        Parse parameters from text line by line.
        
        '''
        if isinstance(lines, list):
            paras = []
            for line in lines:
                para = cls.parse(line)
                if para[0] is not None:
                    paras.append(para)
            return paras
        else:
            name = None
            value = None
            comment = None

            # extract comment
            if '#' in lines:
                pp = lines.strip().split('#', 1)
                pairs, comment = pp
            else:
                pairs = lines

            # filter comment line and read valid parameters
            if '=' in pairs:
                p1, p2 = pairs.split('=', 1)
                ck = [(ig in p2) for ig in '=,;?']  # illegal character
                if any(ck):
                    dsp = 'Only one parameter can be set in one line!\n'
                    dsp2 = '  > {}'.format(lines)
                    raise ValueError(''.join([dsp, dsp2]))
                name = p1.strip().lower()

                if name in ['dperfect', 'ddefect', 'prefix']:
                    value = p2.strip()  # String

                elif name in ['npts', 'bftype']:
                    value = int(p2)  # Int

                elif name in ['ewald', 'epsilon', 'penergy',
                              'evbm', 'ecbm', 'emin', 'emax', 'pvolume']:
                    value = float(p2)  # Float

                elif name in ['valence']:
                    # Int-list
                    value = [int(item) for item in p2.split()]

                elif name in ['cmpot']:
                    # Float-list
                    value = [float(item) for item in p2.split()]

                elif name == 'ddname':
                    # Str or Str-list
                    ck1 = ' ' not in p2.strip()
                    ck2 = p2.lower().startswith('auto')
                    ck3 = p2.lower().startswith('pre')
                    if any([ck1, ck2, ck3]):
                        value = 'auto'
                    else:
                        value = p2.strip().split()
                else:
                    print("WARNING: Undefined Keyword: {} ".format(name))

            return name, value, comment


def formation(inputlist=None, infolevel=1):
    '''
    Calculate defect formation energy.

    '''
    sys.stdout = Logger()

    # Information, version, author
    t = time.localtime(time.time())
    infos = ['Point Defect Formation Energy Calculation - {}'.format(__prog__),
             'Author: {} (v{}, {})'.format(__author__, __version__, __date__),
             'Run at {}'.format(time.strftime("%Y-%m-%d %A %X", t))]
    print(*infos, sep='\n')
    print('')

    # Read InputList
    if inputlist is None:
        ipt = InputList(filein)
    elif isinstance(inputlist, InputList):
        ipt = inputlist
    elif isinstance(inputlist, str):
        ipt = InputList(filename=inputlist)
    else:
        raise RuntimeError('Unrecognized input #1')
    ipt.set_default()
    
    # print('Read input parameters:\n')
    print('{:-^55s}'.format(' INPUT LIST '))
    print(ipt)
    print('-' * 55 + '\n')
    # print('\n')

    # Read Evbm
    if ipt.evbm == float('inf'):
        Eband = read_evbm(
            os.path.join(ipt.dperfect, 'EIGENVAL'))
        Evbm = Eband[0][0]
        Eband_cbm = Eband[1][0]
        print('Read VBM from EIGENVAL: {}'.format(Evbm))
    else:
        Evbm = ipt.evbm
        Eband_cbm = None
        print('Read VBM from INPUT: {}'.format(Evbm))
    
    # Read Ecbm
    if ipt.ecbm == float('inf'):
        if Eband_cbm is None:
            Ecbm = None
            print('Failed to read CBM from neither EIGENVAL nor INPUT.')
        else:
            Ecbm = Eband_cbm
            print('Read CBM from EIGENVAL: {}'.format(Ecbm))
    else:
        Ecbm = ipt.ecbm
        print('Read CBM from INPUT: {}'.format(Ecbm))

    # Read volume of perfect cell
    if ipt.pvolume == float('inf'):
        Volume = read_volume(
            os.path.join(ipt.dperfect, 'OUTCAR'))
        print('Read volume of perfect cell from OUTCAR: {}'.format(Volume))
    else:
        Volume = ipt.pvolume
        print('Read volume of perfect cell from INPUT: {}'.format(Volume))

    # Read Energy of Perfect Cell
    if ipt.penergy == float('inf'):
        Eperfect = read_energy(
            os.path.join(ipt.dperfect, 'OUTCAR'))
        print('Read energy of perfect cell from OUTCAR: {}'.format(Eperfect))
    else:
        Eperfect = ipt.penergy
        print('Read energy of perfect cell from INPUT: {}'.format(Eperfect))

    # Read Energy of defect Cells
    print('Read energy of defect cells from OUTCARs:')
    Edefect = []
    for van, fname in zip(ipt.valence, ipt.ddname):
        Edefect.append(read_energy(
            os.path.join(ipt.ddefect, fname, 'OUTCAR')))
        print('    {:+d}: {}'.format(van, Edefect[-1]))
    print('')

    # chemical potential of elements
    print('Chemical potential of elements (remove-add pairs): ')
    if ipt.cmpot:
        rm, ad = ipt.cmpot[::2], ipt.cmpot[1::2]
        Dcm = sum(rm) - sum(ad)
        dsp = '    {:<12.4f}{:<12.4f}'
        for rmi, adi in zip(rm, ad):
            print(dsp.format(rmi, adi))
        print('  (Total: {:<.4f})'.format(Dcm))
    else:
        print('    Negligible')
    print('')

    # Image-charge correction
    print('Image-charge correction: ', end='')
    ck1 = ipt.ewald == float('inf')
    ck2 = ipt.epsilon == float('inf')
    ck3 = ipt.epsilon > 1E8
    if any([ck1, ck2, ck3]):
        Eic_q2 = 0
        print('Negligible')
    else:
        # 2/3*(q**2)*Ewald/epsilon
        Eic_q2 = 2 / 3 * ipt.ewald / ipt.epsilon
        print('( Eic/q^2 = {:.4f} )'.format(Eic_q2))
    
    # Band-filling correction (alias Moss-Burstein correction)
    print('Band-filling correction: ', end='')
    Ecbf = [0 for _ in range(len(ipt.valence))]
    Evbf = [0 for _ in range(len(ipt.valence))]
    bftype = ipt.bftype
    if bftype == 0:
        print('Negligible')
    else:
        if bftype == -1:
            dsp = 'Only valence bands'
        elif bftype == 1:
            dsp = 'Only conduction bands'
        else:
            bftype = 0
            dsp = 'Both valence and conduction bands'
            
        kptw = []
        eig = []
        ocp = []
        for fname in ipt.ddname:
            fid = os.path.join(ipt.ddefect, fname, 'EIGENVAL')
            *_, (*_, i_kptw), (i_eig, i_ocp) = read_eigval(fid)
            kptw.append(i_kptw)
            eig.append(i_eig)
            ocp.append(i_ocp)
            
        if bftype <= 0:
            Evbf = []
            for i_kptw ,i_eig, i_ocp in zip(kptw, eig, ocp):
                corr_bf = (Evbm > i_eig)*i_kptw*(1-i_ocp)*(Evbm-i_eig)
                Evbf.append(-2*np.sum(corr_bf))           
        if bftype >= 0:
            if Ecbm is None:
                dsp += ' ' * 25
                dsp += '(Failed to correct CB for missed Ecbm)'
            else:
                Ecbf = []
                for i_kptw ,i_eig, i_ocp in zip(kptw, eig, ocp):
                    corr_bf = (i_eig > Ecbm)*i_kptw*i_ocp*(i_eig-Ecbm)
                    Ecbf.append(-2*np.sum(corr_bf))
        print(dsp)
        
        
    # Potential alignment correction
    print('Find defect site(s) for potential alignment correction:')
    # print('Potential alignment correction:')
    # print('Reading POSCARs ...', end='        ')
    pos1 = Cell(os.path.join(ipt.dperfect, 'POSCAR'))
    idx = ipt.valence.index(0) if 0 in ipt.valence else 0
    pos2 = Cell(os.path.join(ipt.ddefect, ipt.ddname[idx], 'POSCAR'))
    idx1, idx2, dmax = pos1.diff(pos2, showdiff=True, out='far')
    print('\nFind the farthest site: ', end='')
    dsp = '{:.4f} at {:s} ({:.4f} {:.4f} {:.4f})'
    print(dsp.format(dmax, pos1.labels[idx1], *pos1.sites[idx1]))

    print('Read electrostatic potential from perfect cell: ', end='')
    pot1 = read_pot(os.path.join(ipt.dperfect, 'OUTCAR'))[idx1]
    print('{:.4f}'.format(pot1))
    print('Read electrostatic potentials from defect cells:')
    pot2 = []
    for van, fname in zip(ipt.valence, ipt.ddname):
        poti = read_pot(os.path.join(ipt.ddefect, fname, 'OUTCAR'))[idx2]
        print('    {:+d}: {:.4f}'.format(van, poti))
        pot2.append(poti)
    print('')

    # Summary
    tableHeader = ['q', 'dE', 'Eq', 'Eic', 'Evbf', 'Ecvf', 'Epa', 'E0']
    print('{:=^80s}'.format(' SUMMARY '))
    print(('{:^10s}' * 8).format(*tableHeader))
    print('-' * 80)
    dsp = '{:^+10d}' + '{:^10.2f}' * 7
    E0q = []
    for q, Ed, dEv, dEc, pot in zip(ipt.valence, Edefect, Evbf, Ecbf, pot2):
        dE = Ed - Eperfect
        Eq = q * Evbm
        Eic = q ** 2 * Eic_q2
        Epa = q * (pot - pot1)
        E0 = dE + Dcm + Eq + Epa + Eic + dEv + dEc
        E0q.append(E0)
        print(dsp.format(q, dE, Eq, Eic, dEv, dEc, Epa, E0))
    print('=' * 80)
    print('*Chemical potential change: {:.2f}'.format(Dcm))
    print('*Energy at VBM: {:.2f}'.format(Evbm))
    print('')

    # calculation
    print('Transtion Energy Level:')
    result, bsdata = cal_trans(q=ipt.valence,
                               H0=E0q,
                               Emin=ipt.emin,
                               Emax=ipt.emax,
                               Npt=ipt.npts,
                               outbsline=True)
    header = ('Valence', 'E_trans/eV', 'E_defect/eV')
    print('  {:^12s}  {:^12s}  {:^12s}'.format(*header))
    dsp = '  {:^12s}  {:^12.2f}  {:^12.2f}'
    for line in result:
        print(dsp.format(*line))
    print('')
    
    # write base energy data to file.(gx = 1)
    # write_bsenergy(data, q, filename=filedata, volume=1, gx=1)
    write_bsenergy(bsdata, ipt.valence, filedata, Volume, 1)

    print('Calculate defect formation energy and write data. (DONE)')
    sys.stdout.stop()


def read_formation(filename, to_reduce=False):
    '''
    Read defect formation energy from data file
    
    Returns
    -------
    (Efermi, energy, charge), volume, gx
    '''
    with open(filename, 'r') as f:
        header = f.readline()
    *_, volume, gx = header.strip().split()
    volume = float(volume)
    gx = float(gx)
    Efermi, energy, charge = np.loadtxt(filename, usecols=(0, 1, 2), unpack=True)

    if to_reduce:
        charge, index = np.unique(charge, return_index=True)
        Efermi = Efermi[index]
        energy = energy[index]
    return (Efermi, energy, charge), volume, gx


def read_H0(filename=filetrans):
    '''
    Read *.trans file or extract *.trans file from log file. In trans file, at 
    least 2 columns must be contained. If more than 2 columns, the 3rd column
    is treated as degenerate factor, and the others are ignored. The end of 2 
    items in title regard as volume and degenerate factor, respectively. 

    Parameters
    ----------
    filename : str, optional
        *.trans file or *.log file.

    Returns
    -------
    data : float list
        List with shape of (N,3), i.e. [(charge, H0, gx),...]
    volume : float
        The volume.

    '''
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    index = [None, None]    # assume file is in *.trans
    for idx, line in enumerate(lines):
        if 'Read volume' in line:
            index[0] = idx
        elif 'SUMMARY' in line:
            index[1] = idx  # confirm *.log
            break
    
    if index[1] != None:
        # read log file and rewrite it to trans file
        pvolume_ = lines[index[0]].strip().split()[-1]
        charge, H0 = [], []
        idx = index[1]+3    # shift pointer to the start of data
        for line in lines[idx:]:
            if '=========' in line:
                break
            else:
                q_, *_, H_ = line.strip().split()
                charge.append(q_)
                H0.append(H_)
        with open(filetrans, 'w') as f:
            f.write('# {} {}\n'.format(pvolume_, 1))
            for qi, hi in zip(charge, H0):
                f.write(' {}   {}   {}\n'.format(qi, hi, 1))
        filename = filetrans
    
    # read data from *.trans file
    with open(filename, 'r') as f:
        header = f.readline()
    *_, volume, gx = header.strip().split()
    volume = float(volume)
    gx = float(gx)
    data = np.loadtxt(filename)
    if data.shape[-1] == 3:
        pass
    elif data.shape[-1] == 2:
        data = np.pad(data, ((0, 0), (0, 1)), constant_values=gx)
    elif data.shape[-1] < 2:
        raise RuntimeError('Charge and H0 columns must be included.')
    else:
        data = data[:, :3]

    return data, volume


def cal_trans(q, H0, Emin=-1, Emax=2, Npt=1001, outbsline=False):
    '''
    Calculate transition levels of charged defect.

    Parameters
    ----------
    q : int list
        Charge list.
    H0 : float list
        Formation energy where Ef is equal to 0.
    Emin : float, optional
        Lower bound of energy window. The default is -1.
    Emax : float, optional
        Upper bound of energy window. The default is 2.
    Npt : int, optional
        Number of sample points. The default is 1001.
    outbsline: bool , optional
        Whether output base energy data. The default is False.

    Returns
    -------
    result : list
        [(Valence_str, E_trans, E_defect),...], \
        [miu, Efmin, qfmin, Eform] (optional)
    '''
    q, H0 = np.array(q), np.array(H0)
    miu = np.linspace(Emin, Emax, Npt).reshape((-1,1))
    Eform = q*miu + H0
    Efmin = Eform.min(axis=-1, keepdims=True)
    q_idx = np.argmin(Eform, axis=-1).reshape((-1,1))
    qfmin = q[q_idx]
    bsdata = np.hstack([miu, Efmin, qfmin, Eform])

    idx = np.unique(q_idx)
    tq = [q[i] for i in idx]
    eq = [H0[i] for i in idx]
    
    result = [('(Begin)', Emin, Efmin[0, 0])]
    dsp2 = '{:+d}/{:+d}'
    for i in reversed(range(1, len(idx))):
        qstr = dsp2.format(tq[i - 1], tq[i])
        E_t = -(eq[i] - eq[i - 1]) / (tq[i] - tq[i - 1])
        E_d = (tq[i] * eq[i - 1] - tq[i - 1] * eq[i]) / (tq[i] - tq[i - 1])
        result.append((qstr, E_t, E_d))
    result.append(('(End)', Emax, Efmin[-1, 0]))
    
    if outbsline:
        return result, bsdata
    else:
        return result

def cal_rdf(cell, atom_idx=(), nhead=30, npad=2, ndigits=1):
    basis = np.array(cell.basis)
    sites = cell.sites
    origin = [sites[atom][idx-1] for atom, idx in atom_idx]
    origin = np.array(origin).reshape((-1, 1, 3))
    
    # produce super cell 
    # npad = 2
    c1, c2, c3 = np.mgrid[-npad:npad+1, -npad:npad+1, -npad:npad+1]
    cc = np.c_[c1.flatten(), c2.flatten(), c3.flatten()]    # shape: (-1, 3)
    
    # claculate distances
    dists_ = [defaultdict(list) for _ in range(len(atom_idx))]  # len: Norg
    pp = sum(sites.values(), start=[])
    pp = np.reshape(np.array(pp), (-1, 1, 1, 3))
    pp = (pp + cc - origin) @ basis             # shape: (Natom, Norg, Nsup, 3)
    pp = np.linalg.norm(pp, ord=2, axis=-1)     # shape: (Natom, Norg, Nsup)
    for (elt, idx, pos), dd in zip(cell.all_pos(), pp):
        for d, dist in zip(dd, dists_):
            for d_i in d:
                dist[(round(d_i, ndigits), elt)].append((idx, pos))

    # nhead = 30
    fillvalue = (0, 'X', 0)         # if site is less than nhead, use fillvalue
    dists = defaultdict(list)
    for (atom, idx), dist in zip(atom_idx, dists_):
        dt = []
        keys = iter(sorted(dist))   # get a generator of sorted keys
        for _ in range(nhead+1):
            key = next(keys, fillvalue)
            dt.append(key+(len(dist[key]), ))   # key: (loc, elt, Ncount)
        dists[tuple(dt)].append(f'{atom}{idx}') # value: label of centre atoms 
    return dists

def write_bsenergy(data, q, filename=filedata, volume=1, gx=1):
    '''
    Write base-energy data to file.

    Parameters
    ----------
    data : TYPE
        DESCRIPTION.
    q : int list
        Charge list.
    volume : float, optional
        Volume of supercell in A^3. The default is 1.
    gx : TYPE, optional
        Degerate factor. The default is 1.

    Returns
    -------
    None.

    '''
    dsp = 'Ef, Eformation, q ' + ', q_{:+d}' * len(q)
    header = dsp.format(*q)
    header += '; {:>12.4f}    {}'.format(volume, gx)
    np.savetxt(filename, data, fmt='%.4f', header=header)

