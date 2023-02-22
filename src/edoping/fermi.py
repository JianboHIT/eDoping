import numpy as np

try:
    from scipy.interpolate import interp1d
    from scipy.optimize import brentq
    try:
        from scipy.integrate import trapezoid
    except:
        from scipy.integrate import trapz as trapezoid
except:
    is_import_scipy = False
else:
    is_import_scipy = True

from .misc import required
from .defect import read_formation, read_H0
from .dft import read_dos


def fd(x):
    '''
    Reduced Fermi-Dirac distribution fd = 1/(1+exp(x))
    '''
    u = np.tanh(x)
    return (1-u)/2


@required(is_import_scipy, 'scipy')
def scfermi_bs(t, doscar='DOSCAR', *filenames):
    '''
    Solve fermi level from base state line
    '''
    kbT = 8.617333262e-05 * t
    dosE, dosV = np.array(read_dos(doscar))   # energy and dos_value
    Nele = trapezoid((dosE<=0)*dosV, dosE)

    defect = []
    for filename in filenames:
        defect_i = read_formation(filename)  # (efermi, eform, q), volume, gx
        defect.append(defect_i)
    formation,volume,gx = zip(*defect)

    Emins = []
    Emaxs = []
    for sample in formation:
        Emins.append(sample[0][0])
        Emaxs.append(sample[-1][0])
    Emin = max([min(Emins), dosE[0]])
    Emax = min([max(Emaxs), dosE[-1]])
    
    f_eform = []
    f_charge = []
    for sample in formation:
        efermi_, eform_, q_ = zip(*sample)
        f_eform.append(interp1d(efermi_, eform_, kind='linear'))
        f_charge.append(interp1d(efermi_, q_, kind='previous'))
    
    @np.vectorize
    def fq1(xfermi):
        '''
        Q1 = sum(q_defect_i)
        '''
        Q1 = 0
        for H, q, g in zip(f_eform, f_charge, gx):
            Q1 += g*q(xfermi)*np.exp(-H(xfermi)/kbT)
        return Q1
    
    @np.vectorize
    def fq2(xfermi):
        '''
        Q2 = n-p
        '''
        Q2 = trapezoid(dosE*fd((dosE-xfermi)/kbT), dosE) - Nele
        return Q2
    
    fqtot = lambda x: fq2(x) - fq1(x)     # net ele, increase with Efermi
        
    if fqtot(Emin) > 0:
        raise RuntimeError('SC-FERMI is bellow EMIN: {}'.format(Emin))
    elif fqtot(Emax) < 0:
        raise RuntimeError('SC-FERMI is above EMAX: {}'.format(Emax))
    else:
        try:
            efermi = brentq(fqtot, Emin, Emax)
        except RuntimeError as err:
            raise err
        except:
            raise RuntimeError('Unknown error!')
        else:
            conc = fq2(efermi)
    conc /= volume.mean()*1E-24      # 1/cell to 1/cm^3
    return efermi, conc


@required(is_import_scipy, 'scipy')
def scfermi_fz(t, conc, charge, volume, doscar='DOSCAR', Evbm=0, detail=False):
    '''
    
    '''
    kbT = 8.617333262e-05 * t
    Q2x = conc * volume * 1E-24
    if Q2x*charge < 0:
        raise RuntimeError('Doping conc. and charge must in same sign.')
        
    dosE, dosV = np.array(read_dos(doscar, efermi=Evbm))   # energy and dos_value
    Nele = trapezoid((dosE<=0)*dosV, dosE)
    
    @np.vectorize
    def fq2(xfermi):
        '''
        Q2 = n-p
        '''
        Q2 = trapezoid(dosV*fd((dosE-xfermi)/kbT), dosE) - Nele
        return Q2
    
    fq2x = lambda x: fq2(x) - Q2x
    amp_max = np.min(np.abs(dosE[[0,-1]]))
    amp = 0.5
    while amp < amp_max:
        if fq2x(-amp)*fq2x(amp) < 0:
            break
        else:
            amp += 0.5
    else:
        raise RuntimeError('Out the energy range of DOS.')
    
    efermi = brentq(fq2x, -amp, amp)
    DHq = -kbT * np.log(Q2x/charge)   # q*exp(-DHq/kbT) = Q2
    DH0 = DHq - charge*efermi       # DHq = DH0 + q*Ef
    if detail:
        return Q2x, DH0, DHq, efermi
    else:
        return DH0, DHq, efermi


@required(is_import_scipy, 'scipy')
def scfermi(t, *filenames, doscar='DOSCAR', Evbm=0, detail=False):
    kbT = 8.617333262e-05 * t
    dosE, dosV = np.array(read_dos(doscar, efermi=Evbm))   # energy and dos_value
    Nele = trapezoid((dosE<=0)*dosV, dosE)
    np.savetxt('data.dat', np.c_[dosE, (dosE<=0)*dosV], fmt='%.4f')
    # print(Evbm, Nele)

    defect = []
    volume = []
    for filename in filenames:
        defect_i, volume_i = read_H0(filename)  # (data: charge, H0, gx),volume
        defect.append(defect_i)
        volume.append(volume_i)
    defect = np.vstack(defect)
    volume = np.array(volume).mean()*1E-24   # A^3 to cm^3
    
    @np.vectorize
    def fq1(xfermi):
        '''
        Q1 = sum(q_defect_i)
        '''
        Q1 = 0
        for q, h, g in defect:
            Q1 += g*q*np.exp(-(h+q*xfermi)/kbT)
        return Q1
    
    @np.vectorize
    def fq2(xfermi):
        '''
        Q2 = n-p
        '''
        Q2 = trapezoid(dosV*fd((dosE-xfermi)/kbT), dosE) - Nele
        return Q2
    
    fqtot = lambda x: fq2(x) - fq1(x)     # net ele, increase with Efermi
    
    amp_max = np.min(np.abs(dosE[[0, -1]]))
    amp = 0.5
    while amp < amp_max:
        if fqtot(-amp)*fqtot(amp) < 0:
            break
        else:
            amp += 0.5
    else:
        raise RuntimeError('Out the energy range of DOS.')
    
    efermi = brentq(fqtot, -amp, amp)
    n_p = fq2(efermi)
    conc = n_p / volume
    
    if detail:
        return n_p, efermi, conc
    else:     
        return efermi, conc
    

def equ_defect(t, *filenames, efermi=(0, ), detail=False):
    '''
    equivalent defect
    '''
    kbT = 8.617333262e-05 * t
    
    defect = []
    for filename in filenames:
        defect_i, *_ = read_H0(filename)  # (data: charge, H0, gx),volume
        defect.append(defect_i)
    defect = np.vstack(defect)    # shape of (N,3)
    charge, H0, gx = np.transpose(defect)       # shape of (N, )
    
    efermi = np.array(efermi).reshape((-1,1))   # shape of (Nf, 1)
    Nq = gx*np.exp(-(H0+charge*efermi)/kbT)     # shape of (Nf, N)
    Ntot = np.sum(Nq, axis=-1, keepdims=True)      # shape of (Nf,1)
    Heff = -kbT*np.log(Ntot)
    Q1 = np.sum(charge*Nq, axis=-1, keepdims=True)
    qeff = Q1/Ntot
    
    header = 'E_fermi q_eff H_eff '
    data = np.hstack([efermi, qeff, Heff])
    if detail:
        header += 'Ntot '
        for q in charge:
            header += 'Nq({}) '.format(q)
        data = np.hstack([data, Ntot, Nq])
    return header, data
        
    
