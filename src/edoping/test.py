import sys, os, time
from defect import *
from dft import *
from fermi import *
from misc import *


def get_argparse2():
    pass


def test(taskid, argv=None):
    '''
    Test & Debug
    
    '''
    
    sys.stdout = Logger(filedebug)
    
    p0 = 'TEST'
    px = 'BUILT-IN TEST'
    
    if taskid == 0:
        infos = {'11': 'read energy',
                 '12': 'read Ewald energy',
                 '13': 'read electrostatic-potentials',
                 '14': 'read vbm, cbm, gap',
                 '15': 'read inputlist',
                 '16': 'compare two POSCARs'}
        print('\nEDOPING - Test & Debug\n')
        for item in infos.items():
            print('  - {:s}  {:s}'.format(*item))
        print('')
    elif taskid == 11:
        dsp1 = '[{:s}] Read energy from OUTCAR ...'
        dsp2 = '[{:s}] Final energy: {:.4f} eV'
        print(dsp1.format(p0))
        value = read_energy()
        print(dsp2.format(p0, value))
    elif taskid == 12:
        dsp1 = '[{:s}] Read (absolute) Ewald from OUTCAR ...'
        dsp2 = '[{:s}] Final Ewald: {:.4f} eV'
        print(dsp1.format(p0))
        value = read_ewald()
        print(dsp2.format(p0, value))
    elif taskid == 13:
        dsp1 = '[{:s}] Read electrostatic potentials from OUTCAR ...'
        dsp2 = '[{:s} BLOCK::START] Electrostatic potentials list:'
        dsp3 = '[{:s} BLOCK::END] Done'
        pf = ' {:>3d} {:<9.4f}'
        print(dsp1.format(p0))
        value = read_pot()
        print(dsp2.format(p0))
        for i, v in enumerate(value, 1):
            print(pf.format(i, v), end='')
            if (i % 5) == 0:
                print('')
        if (i % 5): 
            print('')
        print(dsp3.format(p0))
    elif taskid == 14:
        dsp1 = '[{:s}] Read VBM, CBM, GAP from EIGENVAL ...'
        pf = '[{:s}] {:s}: {:<8.4f} (band #{:<3d}) [{:>9.4f}{:>9.4f}{:>9.4f} ]'
        pfg = '[{:s}] {:s}: {:.4f}'
        print(dsp1.format(p0))
        vb, cb, gp = read_evbm()
        print(pf.format(p0, 'VBM', vb[0], vb[1], *vb[2]))
        print(pf.format(p0, 'CBM', cb[0], cb[1], *cb[2]))
        print(pfg.format(p0, 'GAP', gp))
    elif taskid == 15:
        dsp1 = '[{:s}] Read inputlist ...'
        dsp2 = '[{:s} BLOCK::START] Input parameters:'
        dsp3 = '[{:s} BLOCK::END] Done'
        dsp4 = '[{:s} BLOCK::START] Automatic completion of missing parameters:'
        dsp5 = '[{:s} BLOCK::END] Done'
        print(dsp1.format(p0))
        fn = argv[0] if argv else filein
        ipt = InputList(filename=fn)
        print(dsp2.format(p0))
        print(ipt)
        print(dsp3.format(p0))
        ipt.set_default()
        print(dsp4.format(p0))
        print(ipt)
        print(dsp5.format(p0))
    elif taskid == 16:
        dsp1 = '[{:s}] Compare two POSCARs ...'
        dsp2 = '[{:s} BLOCK::START] Site-to-site comparison:'
        dsp3 = '[{:s} BLOCK::END] Done'
        print(dsp1.format(p0))
        if len(argv) == 0:
            raise Exception('ERROR: At least one POSCAR is required!')
        if len(argv) == 1:
            pos1 = 'POSCAR'
            pos2 = argv[0]
        elif len(argv) > 1:
            pos1, pos2, *_ = argv
        c1 = Cell(poscar=pos1)
        c2 = Cell(poscar=pos2)
        print(dsp2.format(p0))
        c1.diff(c2, showdetail=True, showdiff=True)
        print(dsp3.format(p0))
    
    # BUILT-IN TEST
    elif taskid == 201:
        dsp1 = '[{:s}] Class Cell() details ...'
        dsp2 = '[{:s} BLOCKS] Atoms and number:'
        dsp3 = '[{:s} BLOCKS] Basis vectors:'
        dsp4 = '[{:s} BLOCKS] Positions:'
        dsp4 = '[{:s} BLOCKS] All done'
        print(dsp1.format(px))
        pos = argv[0] if argv else 'POSCAR'
        cell = Cell(poscar=pos)
        print(dsp2.format(px))
        for at, nu in zip(cell.atom_type, cell.atom_num):
            print('      {}({})'.format(at, nu), end='')
        print('')
        print(dsp3.format(px))
        for line in cell.basis:
            print('    ',line)
        print(dsp4.format(px))
        data = zip(cell.atoms, cell.sites, cell.labels)
        for i, (at, site, lb) in enumerate(data, 1):
            print(' {:>3d}  {:.4f} {:.4f} {:.4f}     {}{}'
                  .format(i, *site, at, lb))
        print(dsp5.format(px))
    elif taskid == 202:
        dsp1 = '[{:s}] Find the farthest site to defects ...'
        dsp2 = '[{:s}] Pos1 is from {}, and Pos2 is from {}.'
        dsp3 = '[{:s} BLOCK::START] Site-to-site comparison:'
        dsp4 = '[{:s} BLOCK::END] Done'
        dsp5 = '[{:s}] Find the farthest site:'
        print(dsp1.format(px))
        if len(argv) == 0:
            raise Exception('ERROR: At least one POSCAR is required!')
        elif len(argv) == 1:
            pos1 = 'POSCAR'
            pos2 = argv[0]
        else:
            pos1, pos2, *_ = argv 
        print(dsp2.format(px))
        c1 = Cell(poscar=pos1)
        c2 = Cell(poscar=pos2)
        print(dsp3.format(px))
        idx1, idx2, dmax = c1.diff(c2, showdetail=True, out='far')
        print(dsp4.format(px))
        print(dsp5.format(px))
        print('[{:s}]      index #1: {:d}'.format(px, idx2+1))
        print('[{:s}]      index #2: {:d}'.format(px, idx2+1))
        print('[{:s}]  max. distace: {:.4f}'.format(px, dmax))
        
    else:
        raise ValueError('Unknown debugging code')
    sys.stdout.stop()