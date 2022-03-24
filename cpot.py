from misc import required

try:
    from pymatgen.ext.matproj import MPRester
except:
    is_import_pmg = False
else:
    is_import_pmg = True

try:
    from scipy.optimize import linprog
except:
    is_import_lnp = False
else:
    is_import_lnp = True


@required(is_import_pmg, 'pymatgen')
def test():
    with MPRester() as m:
        m.get_database_version()


def _read_file(filename):
    names = ('A1', 'A2')
    A_eq = None
    b_eq = None
    A_ub = None
    b_ub = None
    bounds = [(None, None)]*3
    return names, (A_ub, b_ub, A_eq, b_eq, bounds)


@required(is_import_lnp, 'scipy')
def pminmax(filename):
    names, constraints = _read_file(filename)


