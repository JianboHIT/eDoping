import re
import json
import urllib.request
import urllib.error
from functools import partial
from multiprocessing import Pool

import numpy as np

from .dft import Cell


def fetch_url(url, timeout=60):
    '''
    Fetch content from the given URL.
    '''
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f'HTTP error: {e.code} - {e.reason}.')
    except (urllib.error.URLError, TimeoutError) as e:
        print(f'URL or Timeout error: {e.reason}')
    except json.JSONDecodeError:
        print('Error decoding JSON data.')
    except Exception as e:  # This catches any other exceptions
        print(f"Unexpected error: {e}")

def query_oqmd(elements, max_ehull=-1, get_struct=False, fields=(),
               timeout=60, batch=200):
    '''
    Query phase data from the OQMD (https://www.oqmd.org/) API.

    Parameters
    ----------
    elements : list of str
        List of chemical element symbols.
    max_ehull : float, optional
        Maximum energy hull filter. If negative, filtering is disabled.
        Default is -1.
    get_struct : bool, optional
        Whether to retrieve structure details. Default is False.
    fields : tuple of str, optional
        Specific fields to retrieve from the API. If empty, defaults to 
        `name`, `entry_id`, `icsd_id`, `formationenergy_id`, `delta_e`,
        and `stability`.
    timeout : float, optional
        The period (in seconds) to await a server reply. Default is 60.
    batch : int, optional
        The number of entries to retrieve in each API request. Default is 200.

    Returns
    -------
    list
        Retrieved phase data.
    '''
    
    if timeout <= 0:
        raise ValueError("Timeout must be greater than 0.")
    
    if batch < 10:
        raise ValueError("Batch size must be 10 or more.")

    default_fields = ('name',
                      'entry_id',
                      'icsd_id',
                      'formationenergy_id',
                      'delta_e',
                      'stability')

    url = 'http://oqmd.org/oqmdapi/formationenergy'
    url += f"?composition={'-'.join(elements)}"
    url += f"&limit={batch}&fields={','.join(fields or default_fields)}"
    url += ',unit_cell,sites' if get_struct else ''
    url += f'&filter=stability<={max_ehull}' if max_ehull >= 0 else ''
    
    content_first = fetch_url(url, timeout)
    ntot = content_first['meta']['data_available']
    
    if ntot > batch:
        worker = partial(fetch_url, timeout=timeout)
        urls = [f'{url}&offset={batch*(i+1)}' for i in range(round(ntot//batch))]
        with Pool() as pool:
            content_others = pool.map(worker, urls)
        contents = [content_first,] + content_others
    else:
        contents = [content_first,]
    
    phases = dict()
    for content in contents:
        if content is not None:
            for data in content['data']:
                name, delta_e = data['name'], data['delta_e']
                if (name not in phases) or (delta_e < phases[name]['delta_e']):
                    phases[name] = data
    return list(phases.values())

def struct2vasp(unit_cell, sites, out=None, comment=None):
    cell = Cell()
    cell.basis = np.array(unit_cell)
    for row in sites:
        atom, _, fa, fb, fc, *_ = row.strip().split()
        fa, fb, fc = float(fa), float(fb), float(fc)
        if atom in cell.sites:
            cell.sites[atom].append(np.array([fa, fb, fc]))
        else:
            cell.sites[atom] = [np.array([fa, fb, fc]),]
    
    if out is not None:
        if not isinstance(out, str):
            raise ValueError('A valid string is required for `out` as filename')
        cell.write(out, header=comment)
    
    return cell
