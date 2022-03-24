import sys, argparse
from defect import formation
from misc import __version__
from dft import ( Cell, read_energy, 
                read_ewald, read_evbm )
from fermi import scfermi_bs
from test import test





def cmd(argv):
    '''
    Parse command line parameter.

    '''
     
    if len(argv) == 1:
        formation()
    else:
        command = argv[1].lower()
        if command in ('help', '-h', '-help','--help'):
            sub = {'energy'  :'Read final energy from OUTCAR',
                   'ewald'   :'Read Ewald from OUTCAR',
                   'evbm'    :'Read VBM from EIGENVAL',
                   'move'    :'Move atom in POSCAR',
                   'scfermi' :'Calculate sc-fermi level'}
            print('Point Defect Formation Energy Calculations', end='')
            print(' - v{}'.format(__version__))
            print('    pydefect [subcommand]\n')
            print('Subcommands:')
            for key, value in sub.items():
                print('    {:<10s}{:s}'.format(key,value))
            print('')
        elif command == 'energy':
            fn = argv[2] if len(argv) > 2 else 'OUTCAR'
            value = read_energy(outcar=fn)
            print('Final energy: {:.4f}'.format(value))
        elif command == 'ewald':
            fn = argv[2] if len(argv) > 2 else 'OUTCAR'
            value = read_ewald(outcar=fn)
            print('Final (absolute) Ewald: {:.4f}'.format(value))
        elif command == 'epsilon':
            pass  # get epsilon
        elif command == 'evbm':
            fn = argv[2] if len(argv) > 2 else 'EIGENVAL'
            pv = float(argv[3]) if len(argv) > 3 else 0.1
            pf = '{:<8.4f} (band #{:<3d}) [{:>9.4f}{:>9.4f}{:>9.4f} ]'
            vb, cb, gp = read_evbm(eigenval=fn, pvalue=pv)
            print(('VBM: '+pf).format(*vb[:2], *vb[2]))
            print(('CBM: '+pf).format(*cb[:2], *cb[2]))
            print('GAP: {:.4f}'.format(gp))      
        elif command == 'move':
            index = int(argv[2]) - 1
            dr = [float(i) for i in argv[3:6]]
            cell = Cell('POSCAR')
            cell.move(index, dr)
            cell.write()
        elif command == 'scfermi':
            temp = float(argv[2])
            dos = argv[3]
            defects = argv[4:]
            EF, Ne = scfermi_bs(temp, doscar=dos, *defects)
            dsp = ('Self-consistent Fermi level (eV)',
                   'Equilibrium carrier concentration (1E20 cm^-3)')
            print('{} : {:.3f}'.format(dsp[0], EF))
            print('{} : {:.4E}'.format(dsp[1], Ne))
        elif command == 'check':
            level = argv[2] if len(argv) > 2 else 1
            if level == 0:
                pass # check filepath
            if level == 1:
                pass # check required file
        elif command == 'debug':
            taskid = argv[2] if len(argv) > 2 else 0
            test(int(taskid), argv[3:])
        elif (command.startswith('-i')
              or command.startswith('input')):
            formation(inputlist=argv[2])
        else:
            raise ValueError('Unknown subcommand')


if __name__ == '__main__':
    cmd(sys.argv)
