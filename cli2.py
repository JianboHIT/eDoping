import argparse
from defect import formation
from misc import filein, fileout
from misc import __prog__, __description__, __version__, __ref__
from dft import Cell, read_energy, read_ewald, read_volume, read_evbm
from fermi import scfermi, scfermi_fz


def get_argparse():
    parser = argparse.ArgumentParser(prog=__prog__,
                                     description='{} - v{}'.format(__description__, __version__),
                                     epilog='If you have used {}, please cite the following article:{}'.format(__prog__, __ref__),
                                     formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-q', '--quiet', action='store_true', help='only show key output')
    sub_parser = parser.add_subparsers(title='Tips', metavar='Subcommand', help='Description', dest='task')

    parser_cal = sub_parser.add_parser('cal', help='Calculate defect fromation energy')
    parser_cal.add_argument('-i', '--input', metavar='FILENAME', default=filein, help='Assign input file name')
    parser_cal.add_argument('-o', '--output', metavar='FILENAME', default=fileout, help='Assign output file name')

    parser_energy = sub_parser.add_parser('energy', help='Read final energy from OUTCAR')
    parser_energy.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename(default: OUTCAR)')

    parser_ewald = sub_parser.add_parser('ewald', help='Read Ewald from OUTCAR')
    parser_ewald.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename(default: OUTCAR)')
    
    parser_volume = sub_parser.add_parser('volume', help='Read volume from OUTCAR')
    parser_volume.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename(default: OUTCAR)')

    # parser_epsilon = sub_parser.add_parser('epsilon', help='Read epsilon from OUTCAR')
    # parser_ewald.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename')

    parser_evbm = sub_parser.add_parser('evbm', help='Read VBM from EIGENVAL')
    parser_evbm.add_argument('-f', '--filename', default='EIGENVAL', help='Assign filename(default: EIGENVAL)')
    parser_evbm.add_argument('-r', '--ratio', type=float, default=0.1, help='Threshold of filling ratio')

    # parser_move = sub_parser.add_parser('move', help='Move atomic position in cell')
    # parser_move.add_argument('index', help='The index of atom needed to displace')
    # parser_move.add_argument('x', type=float, help='x')
    # parser_move.add_argument('y', type=float, help='y')
    # parser_move.add_argument('z', type=float, help='z')

    parser_replace = sub_parser.add_parser('replace', help='Replace atoms X by Y')
    parser_replace.add_argument('old', metavar='X', help='Name of previous atom')
    parser_replace.add_argument('new', metavar='Y', help='Name of new atom')
    parser_replace.add_argument('-i', '--input', metavar='FILENAME', default='POSCAR', help='Input filename(default: POSCAR)')
    parser_replace.add_argument('-o', '--output', metavar='FILENAME', default='POSCAR', help='Output filename(default: POSCAR)')

    parser_scfermi = sub_parser.add_parser('scfermi', help='Calculate sc-fermi level')
    parser_scfermi.add_argument('-t', '--temperature', type=float, default=1000, help='Temperature')
    parser_scfermi.add_argument('filename', metavar='FILENAME', nargs='+', help='Defect formation energy file')
    parser_scfermi.add_argument('-d', '--dos', metavar='DOSDATA', default='DOSCAR', help='DOSCAR(default) or tdos.dat')
    parser_scfermi.add_argument('--vbm', type=float, default=0, help='Energy of VBM(crucial when read DOSCAR, default:0)')

    # (t, conc, charge, volume, doscar='DOSCAR'):
    parser_fzfermi = sub_parser.add_parser('fzfermi', help='Calculate fz-fermi level')
    parser_fzfermi.add_argument('-t', '--temperature', type=float, default=1000, help='Temperature')
    parser_fzfermi.add_argument('-d', '--dos', metavar='DOSDATA', default='DOSCAR', help='DOSCAR(default) or tdos.dat')
    parser_fzfermi.add_argument('--vbm', type=float, default=0, help='Energy of VBM(crucial when read DOSCAR, default:0)')
    parser_fzfermi.add_argument('conc', type=float, help='Conc of carrier in cm^-3')
    parser_fzfermi.add_argument('charge', type=float, help='Charge of defect')
    parser_fzfermi.add_argument('volume', type=float, help='Volume of cell in A^3')

    return parser


def cmd(arg=None):
    parser = get_argparse()
    args = parser.parse_args(arg)

    if args.verbosity > 4:
        # debug mode
        raise NotImplementedError
    
    is_quiet = args.quiet
    is_detail = bool(args.verbosity)

    if args.task == 'cal':
        formation(inputlist=args.input)
    elif args.task == 'energy':
        value = read_energy(outcar=args.filename)
        if is_quiet:
            print('{:.4f}'.format(value))
        else:
            print('Final energy: {:.4f}'.format(value))
    elif args.task == 'ewald':
        value = read_ewald(outcar=args.filename)
        if is_quiet:
            print('{:.4f}'.format(value))
        else:
            print('Final (absolute) Ewald: {:.4f}'.format(value))
    elif args.task == 'volume':
        value = read_volume(outcar=args.filename)
        if is_quiet:
            print('{:.4f}'.format(value))
        else:
            print('Final volume of cell: {:.4f}'.format(value))
    elif args.task == 'evbm':
        vb, cb, gp = read_evbm(eigenval=args.filename, pvalue=args.ratio)
        pf = '{:.4f}'
        pfd = '{:<8.4f} (band #{:<3d}) [{:>9.4f}{:>9.4f}{:>9.4f} ]'
        if is_quiet:
            print(pf.format(cb[0]))  # CBM
        elif is_detail:
            print(('VBM: ' + pfd).format(*vb[:2], *vb[2]))
            print(('CBM: ' + pfd).format(*cb[:2], *cb[2]))
            print(('GAP: ' + pf).format(gp))
        else:
            print(('VBM: ' + pf).format(vb[0]))
            print(('VBM: ' + pf).format(cb[0]))
            print(('GAP: ' + pf).format(gp))
            
    elif args.task == 'replace':
        pos = Cell(poscar=args.input)
        pos.replace(args.old, args.new)
        pos.write(poscar=args.output)
        dsp = 'Replace {} by {}, and new POSCAR is saved to {}'
        if not is_quiet:
            print(dsp.format(args.old, args.new, args.output))
    elif args.task == 'scfermi':
        # scfermi(t, *filenames, doscar='DOSCAR', Evbm=0, detail=False)
        out = scfermi(args.temperature, 
                      *args.filename, 
                      doscar=args.dos, 
                      Evbm=args.vbm,
                      detail=is_detail)
        dsp = ('Self-consistent Fermi level (eV)',
               'Equilibrium carrier concentration (cm^-3)',
               'Net number of electron in cell')
        if is_quiet:
            # not_detail: EF, Ne
            #  is_detail: n_p, EF, Ne 
            print(*out)
        elif is_detail:
            n_p, EF, Ne = out
            print('{} : {:.3f}'.format(dsp[0], EF))
            print('{} : {:.4E}'.format(dsp[1], Ne))
            print('{} : {:+.6E}'.format(dsp[2], n_p))
        else:
            EF, Ne = out
            print('{} : {:.3f}'.format(dsp[0], EF))
            print('{} : {:.4E}'.format(dsp[1], Ne))
    elif args.task == 'fzfermi':
        # scfermi_fz(t, conc, charge, volume, doscar='DOSCAR', Evbm=0)
        out = scfermi_fz(t=args.temperature, 
                         conc=args.conc, 
                         charge=args.charge, 
                         volume=args.volume, 
                         doscar=args.dos,
                         Evbm=args.vbm,
                         detail=is_detail)
        dsp = ('Formation energy: H(Ef) = {:.2f} {:+.3f}*Ef',
               'Formation energy at sc-Ef({:.2f} eV): {:.2f} eV/u.c.',
               'Net number of electron in cell: {:+.6E}')
        if is_quiet:
            # not_detail: DH0, DHq, Ef
            #  is_detail: n_p, DH0, DHq, Ef
            print(*out)      
        elif is_detail:
            n_p, DH0, DHq, Ef = out
            print(dsp[0].format(DH0, args.charge))
            print(dsp[1].format(Ef, DHq))
            print(dsp[2].format(n_p))
        else:
            DH0, DHq, Ef = out
            print(dsp[0].format(DH0, args.charge))
            print(dsp[1].format(Ef, DHq))


if __name__ == '__main__':
    cmd()
