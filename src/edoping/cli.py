#!/usr/bin/env python3

import argparse
import re
from .defect import formation, read_H0, cal_trans, cal_rdf, \
                    diff_cell, disp_diffs, move_pos, write_bsenergy
from .misc import filein, filecmpot, filetrans, filedata, \
                  __prog__, __description__, __version__, __ref__
from .dft import Cell, read_energy, read_ewald, read_volume, \
                 read_evbm, read_evbm_from_ne, read_epsilon, read_zval, \
                 fix_charge
from .fermi import scfermi, scfermi_fz, equ_defect
from .query import query_oqmd, struct2vasp
from .cpot import pminmax


def cmd(arg=None):
    footnote = f'>>>>>>>>>> Citation of {__prog__} <<<<<<<<<<\n'\
               f'If you have used {__prog__}, '\
               f'please cite the following article:{__ref__}'
    parser = argparse.ArgumentParser(prog=__prog__.lower(),
                                     description='{} - v{}'.format(__description__, __version__),
                                     formatter_class=argparse.RawDescriptionHelpFormatter, 
                                     epilog=footnote)
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity')
    parser.add_argument('-q', '--quiet', action='store_true', help='only show key output')
    sub_parser = parser.add_subparsers(title='Tips', metavar='Subcommand', help='Description', dest='task')

    parser_cal = sub_parser.add_parser('cal', help='Calculate defect fromation energy')
    parser_cal.add_argument('-i', '--input', metavar='FILENAME', default=filein, help=f'Assign filename (default: {filein})')

    parser_energy = sub_parser.add_parser('energy', help='Read final energy from OUTCAR')
    parser_energy.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename(default: OUTCAR)')
    parser_energy.add_argument('--ave', '--average', action='store_true', help='Calculate energy per atom')

    parser_ewald = sub_parser.add_parser('ewald', help='Read Ewald from OUTCAR')
    parser_ewald.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename(default: OUTCAR)')
    
    parser_volume = sub_parser.add_parser('volume', help='Read volume from OUTCAR')
    parser_volume.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename(default: OUTCAR)')

    parser_epsilon = sub_parser.add_parser('epsilon', help='Read epsilon from OUTCAR')
    parser_epsilon.add_argument('-f', '--filename', default='OUTCAR', help='Assign filename(default: OUTCAR)')

    parser_evbm = sub_parser.add_parser('evbm', help='Read VBM from EIGENVAL')
    parser_evbm.add_argument('-f', '--filename', default='EIGENVAL', help='Assign filename(default: EIGENVAL)')
    parser_evbm.add_argument('-r', '--ratio', type=float, help='Threshold of filling ratio')
    parser_evbm.add_argument('--ne', type=int, help='The number of electrons(default from the file)')
    parser_evbm.add_argument('--amend', type=int, default=0, help='Additional amendment on nelect')

    parser_fixchg = sub_parser.add_parser('fixchg', help='Produce charge-fixed inputs')
    parser_fixchg.add_argument('-i', '--inputdir', default='charge_0', help='Path to uncharged (q=0) reference files (default: charge_0)')
    parser_fixchg.add_argument('--prefix', default='charge_', help='Prefix of charge-fixed output files (default: charge_)')
    parser_fixchg.add_argument('charges', metavar='CHARGE', type=int, nargs='+', help='The target charge(s)')

    parser_boxhyd = sub_parser.add_parser('boxhyd', help='Place a single hydrogen atom in the box')
    parser_boxhyd.add_argument('-i', '--input', metavar='FILENAME', default='POSCAR', help='Reference structure(default: POSCAR)')
    parser_boxhyd.add_argument('-o', '--output', metavar='FILENAME', default='POSCAR.H', help='Output filename(default: POSCAR.H)')

    parser_move = sub_parser.add_parser('move', help='Move atomic position in cell')
    parser_move.add_argument('index', type=int, help='The index of atom needed to displace')
    parser_move.add_argument('x', type=float, default=0, help='Displacement along x-axis direction')
    parser_move.add_argument('y', type=float, default=0, help='Displacement along y-axis direction')
    parser_move.add_argument('z', type=float, default=0, help='Displacement along z-axis direction')
    parser_move.add_argument('-c', '--cartesian', action='store_true', help='Displacement is given in Cartesian system')
    parser_move.add_argument('-i', '--input', metavar='FILENAME', default='POSCAR', help='Input filename(default: POSCAR)')
    parser_move.add_argument('-o', '--output', metavar='FILENAME', default='POSCAR', help='Output filename(default: POSCAR)')

    parser_replace = sub_parser.add_parser('replace', help='Replace atoms X by Y')
    parser_replace.add_argument('old', metavar='X', help='Name of previous atom')
    parser_replace.add_argument('new', metavar='Y', help='Name of present atom')
    parser_replace.add_argument('-p', '--position', type=float, nargs=3, metavar='X', help='Position of new interstitial atom')
    parser_replace.add_argument('-i', '--input', metavar='FILENAME', default='POSCAR', help='Input filename(default: POSCAR)')
    parser_replace.add_argument('-o', '--output', metavar='FILENAME', default='POSCAR', help='Output filename(default: POSCAR)')
    
    parser_groupby = sub_parser.add_parser('groupby', help='Group atoms by radial distribution function')
    parser_groupby.add_argument('-f', '--filename', default='POSCAR', help='Assign filename(default: POSCAR)')
    parser_groupby.add_argument('atom', metavar='ATOM', help='The name of element to groupby')
    parser_groupby.add_argument('--head', type=int, default=30, help='The number of atoms in the nearest neighbor(default: 30)')
    parser_groupby.add_argument('--pad', type=int, default=2, help='Number of values padded to the cell sides(default: 2)')
    parser_groupby.add_argument('--digits', type=int, default=1, help='Given precision in decimal digits(default: 1)')
    parser_groupby.add_argument('--grep', metavar='STRING', help='Display only lines containing the specified string')
    
    parser_diff = sub_parser.add_parser('diff', help='Show difference between two POSCAR')
    parser_diff.add_argument('-p', '--prec', type=float, default=0.2, help='The precision of distance(default: 0.2)')
    parser_diff.add_argument('-d', '--distance', action='store_true', help='Calculate sum of distances between sites and detected defects')
    parser_diff.add_argument('filename1', help='Filename of the first POSCAR')
    parser_diff.add_argument('filename2', help='Filename of the second POSCAR')
    
    parser_query = sub_parser.add_parser('query', help='Fetch data from OQMD website')
    parser_query.add_argument('-s', '--structure', action='store_true', help='Fetch structure files at same time')
    parser_query.add_argument('-x', '--extra', default='', help='Extra elements beyond host compound')
    parser_query.add_argument('-t', '--timeout', type=float, default=60, help='The period (in seconds) to await a server reply (default: 60)')
    parser_query.add_argument('-e', '--ehull', type=float, default=-1, help='Maximum energy hull filter. If negative (default), filtering is disabled')
    parser_query.add_argument('-b', '--batch', type=int, default=200, help='The number of entries to retrieve in each request (default: 200)')
    parser_query.add_argument('-o', '--output', metavar='FILENAME', default=filecmpot, help=f'Output filename(default: {filecmpot})')
    parser_query.add_argument('compound', help='The target compound, e.g. Mg2Si')

    parser_chempot = sub_parser.add_parser('chempot', help='Calculate chemical potential')
    parser_chempot.add_argument('-n', '--norm', action='store_true', help='Enable coefficients normalization (if energy/atom is given)')
    parser_chempot.add_argument('-f', '--filename', default=filecmpot, help='Assign filename(default: {})'.format(filecmpot))
    parser_chempot.add_argument('--cond', metavar='WEIGHT', type=float, nargs='+', help='Customized chemical potential conditions')
    parser_chempot.add_argument('--refs', metavar='VALUE', type=float, nargs='+', help='Reference chemical potentials in eV/atom')

    parser_trlevel = sub_parser.add_parser('trlevel', help='Calculate transition levels')
    parser_trlevel.add_argument('-f', '--filename', default=filetrans, help='Assign filename(default: {})'.format(filetrans))
    parser_trlevel.add_argument('--emin', type=float, default=-1, help='The upper bound of Fermi level(default: -1)')
    parser_trlevel.add_argument('--emax', type=float, default= 2, help='The lower bound of Fermi level(default: 2)')
    parser_trlevel.add_argument('-n', '--npoints', type=int, default=1001, help='The number of points(default: 1001)')
    parser_trlevel.add_argument('--fenergy', action='store_true', help='To calculate formation energy')
    parser_trlevel.add_argument('-o', '--output', metavar='FILENAME', default=filedata, help='Output filename(default: {})'.format(filedata))

    parser_scfermi = sub_parser.add_parser('scfermi', help='Calculate sc-fermi level')
    parser_scfermi.add_argument('-t', '--temperature', type=float, default=1000, help='Temperature')
    parser_scfermi.add_argument('filename', metavar='FILENAME', nargs='+', help='Defect formation energy file (*.trans or *.log)')
    parser_scfermi.add_argument('-d', '--dos', metavar='DOSDATA', default='DOSCAR', help='DOSCAR(default) or tdos.dat')
    parser_scfermi.add_argument('--vbm', type=float, default=0, help='Energy of VBM (quite necessary, default:0)')

    # (t, conc, charge, volume, doscar='DOSCAR'):
    parser_fzfermi = sub_parser.add_parser('fzfermi', help='Calculate fz-fermi level')
    parser_fzfermi.add_argument('-t', '--temperature', type=float, default=1000, help='Temperature')
    parser_fzfermi.add_argument('-d', '--dos', metavar='DOSDATA', default='DOSCAR', help='DOSCAR(default) or tdos.dat')
    parser_fzfermi.add_argument('--vbm', type=float, default=0, help='Energy of VBM (quite necessary, default:0)')
    parser_fzfermi.add_argument('conc', type=float, help='Conc of carrier in cm^-3')
    parser_fzfermi.add_argument('charge', type=float, help='Charge of defect')
    parser_fzfermi.add_argument('volume', type=float, help='Volume of cell in A^3')

    # TODO: # (t, *filenames, efermi=(0, ), detail=False)
    # parser_equi = sub_parser.add_parser('equi', help='Confirm the equivalent defect')
    # parser_equi.add_argument('-t', '--temperature', type=float, default=1000, help='Temperature')
    # parser_equi.add_argument('filename', metavar='FILENAME', nargs='+', help='Defect formation energy file')
    # parser_equi.add_argument('--fermi', type=float, nargs='+', default=[0,], help='Fermi level')
    # parser_equi.add_argument('--emin', type=float, default=0, help='The upper bound of Fermi level(default: 0)')
    # parser_equi.add_argument('--emax', type=float, default=1, help='The lower bound of Fermi level(default: 1)')
    # parser_equi.add_argument('-n', '--npoints', type=int, default=0, help='The number of points')
    # parser_equi.add_argument('-r', '--ratio', action='store_true', help='only show key output')
    
    args = parser.parse_args(arg)

    if args.verbosity > 4:
        # debug mode
        raise NotImplementedError
    
    is_quiet = args.quiet
    is_detail = bool(args.verbosity)

    if args.task is None:
        parser.print_help()
    elif args.task == 'cal':
        formation(inputlist=args.input)
    elif args.task == 'energy':
        value = read_energy(outcar=args.filename, average=args.ave)
        unit = 'eV/atom' if args.ave else 'eV/cell'
        if is_quiet:
            print('{:.4f}'.format(value))
        else:
            print('Final energy: {:.4f} {}'.format(value, unit))
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
    elif args.task == 'epsilon':
        # read_epsilon(outcar='OUTCAR', isNumeric=False)
        pf = '{:12.4f}'
        if is_quiet:
            out = read_epsilon(outcar=args.filename, isNumeric=True)
            for _, values in out:
                for value in values:
                    for ivalue in value:
                        print(pf.format(ivalue), end='')
                    print()
        else:
            out = read_epsilon(outcar=args.filename)
            for title, values in out:
                print(title)
                for value in values:
                    print(value)
    elif args.task == 'evbm':
        if args.ratio is not None:
            vb, cb, gp = read_evbm(eigenval=args.filename, pvalue=args.ratio)
        else:
            vb, cb, gp = read_evbm_from_ne(eigenval=args.filename,
                                           Ne=args.ne,
                                           dNe=args.amend)
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
            print(('CBM: ' + pf).format(cb[0]))
            print(('GAP: ' + pf).format(gp))
    elif args.task == 'fixchg':
        # Read ZVAL from POTCAR && Check consistency with POSCAR
        if is_detail:
            print('Parsing number of valence electrons from POTCAR and POSCAR in {}...'.format(args.inputdir))
        z_dict = read_zval(potcar='{}/POTCAR'.format(args.inputdir))
        pos = Cell(poscar='{}/POSCAR'.format(args.inputdir))
        epos = ' '.join(pos.sites.keys())
        epot = ' '.join(z_dict.keys())
        if epos != epot:
            raise ValueError('Elements in {0}/POSCAR and {0}/POTCAR are not consistent:\n'
                                '    [{}] vs. [{}]'.format(args.inputdir, epos, epot))

        # Calculate total valence electrons
        total = 0
        for atom, site in pos.sites.items():
            if atom not in z_dict:
                raise ValueError('Cannot find infomation of {} in {}/POTCAR'.format(atom, args.inputdir))
            zi = z_dict[atom]
            num = len(site)
            total += num * zi
            if is_detail:
                print('{:>4s}: {:3g}   ( {} )'.format(atom, zi, num))
        if is_quiet:
            print('{:g}'.format(total))
        else:
            print('Total valence electrons: {:g}'.format(total))

        # Reset NELECT for each provided charge number
        import shutil

        for q in args.charges:
            outdir = '{}{:+g}'.format(args.prefix, q)
            shutil.copytree(args.inputdir, outdir)
            fix_charge('{}/INCAR'.format(outdir), charge=q, nelect=total)
            if not is_quiet:
                print('Produce directory {} successfully.'.format(outdir))
    elif args.task == 'boxhyd':
        pos = Cell(poscar=args.input)
        poshyd = Cell()
        poshyd.basis = pos.basis
        poshyd.sites['H'] = [[0,0,0]]
        poshyd.write(args.output)
        if not is_quiet:
            dsp='The new POSCAR is saved to {}'
            print(dsp.format(args.output))
    elif args.task == 'move':
        pos = Cell(poscar=args.input)
        index = args.index - 1   # convert common 1-start to pythonic 0-start
        atom, idx, site = list(pos.all_pos())[index]
        dr = [args.x, args.y, args.z]
        site2 = move_pos(site, pos.basis, dr, cartesian=args.cartesian)
        pos.sites[atom][idx-1] = site2
        pos.write(poscar=args.output)
        if not is_quiet:
            if is_detail:
                dsp1 = 'Displacement: [{:.2f}, {:.2f}, {:.2f}]'
                dsp2 = ' {}{}: ({:.4f}, {:.4f}, {:.4f}) --> ({:.4f}, {:.4f}, {:.4f})'
                print(dsp1.format(*dr))
                print(dsp2.format(atom, idx, *site, *site2))
            dsp='The new POSCAR is saved to {}'
            print(dsp.format(args.output))
    elif args.task == 'replace':
        poscar = Cell(poscar=args.input)
        old = re.match(r'([a-zA-Z]+)(\d*)', args.old)
        if old:
            atom, idx = old.groups()
            atom_old = {
                'atom': atom,
                'idx': int(idx) if idx else 1
            }
        else:
            raise ValueError('Invaild value: {}'.format(args.old))

        if atom_old['atom'].lower().startswith('vac'):
            if args.position is None:
                raise ValueError('Position of interstitial atom is required by --position option.')
            loc = args.position
        else:
            loc = poscar.pop(**atom_old)

        new = re.match(r'([a-zA-Z]+)', args.new)
        if new:
            atom_new = {
                'atom': new.groups()[0],
                'pos': loc
            }
        else:
            raise ValueError('Invaild value: {}'.format(args.new))

        if not atom_new['atom'].lower().startswith('vac'):
            poscar.insert(**atom_new)

        poscar.write(poscar=args.output)
        dsp = 'Replace {} by {}, and new POSCAR is saved to {}'
        if not is_quiet:
            label_old = '{}{}'.format(atom_old['atom'], atom_old['idx'])
            label_new = '{}'.format(atom_new['atom'])
            print(dsp.format(label_old, label_new, args.output))
    elif args.task == 'groupby':
        pos = Cell(poscar=args.filename)
        Natom = len(pos.sites[args.atom])
        kwargs = {
            'atom_idx': [(args.atom, idx+1) for idx in range(Natom)],
            'nhead': args.head,
            'npad': args.pad,
            'ndigits': args.digits,
        }
        dists = cal_rdf(pos, **kwargs)
        infos = list(dists.keys())
        for i, k in enumerate(infos):
            print('Group #{}: {}'.format(i+1, ', '.join(dists[k])))
        if not is_quiet:
            print()
            headers = ['Group #{}'.format(i+1) for i in range(len(infos))]
            print('===={}'.format('='.join(['='*18 for _ in headers])))
            print('No.|{}'.format('|'.join(['{:^18s}'.format(header) for header in headers])))
            print('---+{}'.format('+'.join(['-'*18 for _ in headers])))
            for i, dts in enumerate(zip(*infos)):
                contents = ['{}'.format(dt) for dt in dts]
                line = '{:^3d}|{}'.format(i, '|'.join(['{:^18s}'.format(cont) for cont in contents]))
                if (not args.grep) or ("'{}'".format(args.grep) in line): print(line)
            print('===={}'.format('='.join(['='*18 for _ in headers])))
    elif args.task == 'diff':
        c1 = Cell(poscar=args.filename1)
        c2 = Cell(poscar=args.filename2)
        diffs = diff_cell(c1, c2, prec=args.prec)
        disp_diffs(c1.basis, diffs,
                   full_list=is_detail,
                   with_dist=args.distance)
    elif args.task == 'query':
        elmt_comp = re.findall(r'[A-z][a-z]*', args.compound)
        elmt_extra = re.findall(r'[A-z][a-z]*', args.extra)
        elmt_all = list(elmt_comp)
        for elt in elmt_extra:
            if elt not in elmt_all:
                elmt_all.append(elt)
        # elmt_all = sorted(set(elmt_comp + elmt_extra))
        if not is_quiet:
            print(f'Searching for phases with elements: {elmt_all}')
        phases = query_oqmd(elements=elmt_all,
                            max_ehull=args.ehull,
                            get_struct=args.structure,
                            timeout=args.timeout,
                            batch=args.batch)
        if not is_quiet:
            print(f'Number of phases retrieved from the database: {len(phases)}')
        
        get_comp = lambda name: {m[0]: int(m[1] or '1') 
            for m in re.findall(r'([A-Z][a-z]*)(\d*\.\d+|\d+)?', name)}
        
        outs = ['# {}\n'.format('   '.join(elmt_all)), ]    # header line
        dsp = ' {} '*(len(elmt_all)+1) + '\n'
        dsp_head = f'POSCAR generated by {__prog__}: '\
                  '{name} (id: {entry_id}) {delta_e} {stability}'
        dsp_fout = 'POSCAR.{name}.vasp'
        dsp_disp = '    {name:<10} {delta_e:>12.6f}      id: {entry_id}'
        
        target = get_comp(args.compound)
        outs.append(dsp.format(*[target.get(e, 0) for e in elmt_all], '_Not_found_'))
        target_found = False

        if is_detail:
            print('   name             delta_e      OQMD_ids')
        with_struct = args.structure
        for phase in phases:
            comp = get_comp(phase['name'])
            ratios = [comp.get(e, 0) for e in elmt_all]
            delta_e = phase['delta_e']
            line = dsp.format(*ratios, delta_e)
            if comp == target:
                outs[1] = line
                target_found = True
            else:
                outs.append(line)
            if with_struct:
                struct2vasp(
                    unit_cell=phase['unit_cell'],
                    sites=phase['sites'],
                    out=dsp_fout.format(**phase),
                    comment=dsp_head.format(**phase),
                )
            if is_detail:
                print(dsp_disp.format(**phase))
        with open(args.output, 'w') as f:
            f.writelines(outs)
        if not is_quiet:
            end_info = '. (DONE)' if target_found else '\n'
            print(f'Data saved to {args.output}{end_info}')
        if not target_found:
            print('*************************** WARNING ***************************\n'
                 f' Failed to fetch the entry of {args.compound} due to network\n'
                  ' issues. Please try again later, use another network, or you\n'
                  ' might prepare the file manually.\n'
                  '***************************************************************\n')
    elif args.task == 'chempot':
        # pminmax(filename, objcoefs=None)
        # return (name, x0, status, msg),labels
        results,labels = pminmax(args.filename, 
                                 objcoefs=args.cond,
                                 referance=args.refs,
                                 normalize=args.norm)
        if is_quiet:
            for rst in results:
                if is_detail:
                    print('{:^5d}'.format(rst[2]), end='')
                if rst[1] is None:
                    raise RuntimeError(f'No solution found\n  {rst[3]}')
                for miu in rst[1]:
                    print('{:<10.4f}'.format(miu), end='')
                print()
        else:
            dsp1 = '{:^8d}{:<10s}'
            dsp2 = '{:>10.4f}'
            dsp3 = '   {:<s}'
            
            header = '{:8s}{:10s}'.format('status', 'condition')
            for elmt in labels:
                header += '{:>10s}'.format('miu('+elmt+')')
            if is_detail:
                header += '   {:<s}'.format('Information')  
            print(header)
            
            for rst in results:
                print(dsp1.format(rst[2], rst[0]), end='')
                if rst[1] is None:
                    raise RuntimeError(f'No solution found\n  {rst[3]}')
                for miu in rst[1]:
                    print(dsp2.format(miu), end='')
                if is_detail:
                    print(dsp3.format(rst[3]))
                else:
                    print()
    elif args.task == 'trlevel':
        data, volume = read_H0(args.filename)
        q, H0 = data[:,0].astype('int32'), data[:,1]
        result, bsdata = cal_trans(q, H0, args.emin, args.emax, 
                                   Npt=args.npoints, outbsline=True)
        if not is_quiet:
            header = ('Valence', 'E_trans/eV', 'E_defect/eV')
            print('  {:^12s}  {:^12s}  {:^12s}'.format(*header))  
        dsp = '  {:^12s}  {:^12.2f}  {:^12.2f}'
        for line in result:
            print(dsp.format(*line))
        print()
        
        if args.fenergy:
            write_bsenergy(bsdata, q, args.output, volume, 1)
            if not is_quiet and is_detail:
                print('Save formation eneryg data to {}.'.format(args.output))
        
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
    elif args.task == 'equi':
        # equ_defect(t, *filenames, efermi=(0, ), detail=False)
        # not_detail: header, (Ef, q_eff, H_eff)
        #  is_detail: header, (Ef, q_eff, H_eff, Ntot, Nq)
        if args.npoints == 0:
            fermi = args.fermi
        else:
            E0, E1, N = args.emin, args.emax, args.npoints
            dE = (E1-E0)/N
            fermi = [E0+i*dE for i in range(N+1)]
        out = equ_defect(args.temperature,
                         *args.filename,
                         efermi=fermi,
                         detail=is_detail)
        
        def disp(data, header=None):
            if header is not None:
                print(header)
            for dd in data:
                Ef, q_eff, H_eff, *Nq = dd
                print('{:10.4f}{:10.4f}{:10.4f}'.format(Ef, q_eff, H_eff),end='')
                for ni in Nq:
                    print('{:10.3E}'.format(ni), end='')
                print()
        
        header, data = out
        if is_detail and args.ratio:
            data[:,4:] /= data[:,3:4]
            
        if is_quiet:
            disp(data)
        else:
            disp(data, header)


if __name__ == '__main__':
    cmd()
