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
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity',)
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
    parser_scfermi.add_argument('-d', '--dos', metavar='DOSDATA', default='DOSCAR', help='DOSCAR or tdos.dat')

    # (t, conc, charge, volume, doscar='DOSCAR'):
    parser_fzfermi = sub_parser.add_parser('fzfermi', help='Calculate fz-fermi level')
    parser_fzfermi.add_argument('-t', '--temperature', type=float, default=1000, help='Temperature')
    parser_fzfermi.add_argument('-d', '--dos', metavar='DOSDATA', default='DOSCAR', help='DOSCAR or tdos.dat')
    parser_fzfermi.add_argument('conc', type=float, help='Conc of carrier in cm^-3')
    parser_fzfermi.add_argument('charge', type=float, help='Charge of defect')
    parser_fzfermi.add_argument('volume', type=float, help='Volume of cell in A^3')

    return parser


def cmd(arg=None):
    parser = get_argparse()
    args = parser.parse_args(arg)

    if args.verbosity > 5:
        # debug mode
        return None
    elif args.verbosity > 0:
        is_detail = True
    else:
        is_detail = False

    if args.task == 'cal':
        formation(inputlist=args.input)
    elif args.task == 'energy':
        value = read_energy(outcar=args.filename)
        print('Final energy: {:.4f}'.format(value))
    elif args.task == 'ewald':
        value = read_ewald(outcar=args.filename)
        print('Final (absolute) Ewald: {:.4f}'.format(value))
    elif args.task == 'volume':
        value = read_volume(outcar=args.filename)
        print('Final volume of cell: {:.4f}'.format(value))
    elif args.task == 'evbm':
        vb, cb, gp = read_evbm(eigenval=args.filename, pvalue=args.ratio)
        pf = '{:<8.4f} (band #{:<3d}) [{:>9.4f}{:>9.4f}{:>9.4f} ]'
        print(('VBM: ' + pf).format(*vb[:2], *vb[2]))
        print(('CBM: ' + pf).format(*cb[:2], *cb[2]))
        print('GAP: {:.4f}'.format(gp))
    elif args.task == 'replace':
        pos = Cell(poscar=args.input)
        pos.replace(args.old, args.new)
        pos.write(poscar=args.output)
        dsp = 'Replace {} by {}, and new POSCAR is saved to {}'
        print(dsp.format(args.old, args.new, args.output))
    elif args.task == 'scfermi':
        EF, Ne = scfermi(args.temperature, doscar=args.dos, *args.filename)
        dsp = ('Self-consistent Fermi level (eV)',
               'Equilibrium carrier concentration (1E20 cm^-3)')
        print('{} : {:.3f}'.format(dsp[0], EF))
        print('{} : {:.4E}'.format(dsp[1], Ne))
    elif args.task == 'fzfermi':
        DH0, DHq = scfermi_fz(args.temperature, args.conc, args.charge, args.volume, args.dos)
        dsp = ('Formation energy: H(Ef) = {:.2f}{:+.3f}*Ef',
               'Formation energy at sc-Ef: {:.2f} eV')
        print(dsp[0].format(DH0, args.charge))
        print(dsp[1].format(DHq))


if __name__ == '__main__':
    cmd()
