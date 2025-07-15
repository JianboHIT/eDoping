#   Copyright 2023-2025, Jianbo Zhu, Jingyu Li, Peng-Fei Liu
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


import json
import urllib.request
import urllib.parse
import urllib.error
from functools import partial
from itertools import combinations
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from .dft import Cell


def fetch_url(url, timeout=60, headers=None):
    '''
    Fetch content from the given URL.
    '''
    err_log = ''
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        err_log = f'HTTP error: {e.code} - {e.reason}.\n'
    except urllib.error.URLError as e:
        err_log = f'URL error: {e.reason}.\n'
    except TimeoutError:
        err_log = f'Timeout error: Please try again later, or use another network.\n'
    except json.JSONDecodeError:
        err_log = f'Error decoding JSON data.\n'
    except Exception as e:  # This catches any other exceptions
        err_log = f'Unexpected error: {e}\n'
    finally:
        # print('[GET]', url, '  ...', 'failed' if err_log else 'done') # for debug
        print(err_log, end='')

def query_oqmd(params, timeout=60, batch=200, include_struct=False):
    '''
    Request data from the OQMD (https://www.oqmd.org/) database.

    Parameters
    ----------
    params : dict
        Query parameters.
    timeout : float, optional
        The period (in seconds) to await a server reply. Default is 60.
    batch : int, optional
        The number of entries to retrieve in each API request. Default is 200.
    include_struct : bool, optional
        Whether to include crystal structure details. Default is False.

    Returns
    -------
    list
        Retrieved data.
    '''
    request = partial(fetch_url, timeout=timeout, headers={})
    url = 'http://oqmd.org/oqmdapi/formationenergy?'
    url += urllib.parse.urlencode(params)

    content_first = request(url)
    ntot = content_first['meta']['data_available']

    if ntot > batch:
        urls = [f'{url}&offset={batch*(i+1)}' for i in range(round(ntot//batch))]
        with ThreadPoolExecutor() as executor:
            content_others = list(executor.map(request, urls))
        contents = [content_first,] + content_others
    else:
        contents = [content_first,]

    datas = list()
    for content in contents:
        if content is None:
            continue
        datas.extend(content['data'])
    if include_struct:
        for data in datas:
            cell = Cell()
            cell.basis = np.array(data['unit_cell'])
            for row in data['sites']:
                atom, _, fa, fb, fc, *_ = row.strip().split()
                fa, fb, fc = float(fa), float(fb), float(fc)
                if atom in cell.sites:
                    cell.sites[atom].append(np.array([fa, fb, fc]))
                else:
                    cell.sites[atom] = [np.array([fa, fb, fc]),]
            data['struct'] = cell
    return datas

def _get_mp_api_headers():
    # Access the api-key of Materials Project database
    # Two ways to configure the API-key:
    #   1. Set the environment variable MP_API_KEY. (Recommended)
    #   2. Add the API key to the file "~/.config/.pmgrc.yaml". (May be 
    #      deprecated in the future)

    import os, sys, platform
    from .misc import __prog__, __version__

    api_key = os.getenv('MP_API_KEY', None)
    if api_key is None:
        # This implementation handles only the simplest scenario: locating
        # the first line in the configuration file that contains 'API_KEY'
        # and extracting its value.
        conf_path = os.path.join(os.path.expanduser("~"), ".config", ".pmgrc.yaml")
        with open(conf_path, "r") as f:
            for line in f:
                if 'API_KEY' in line:
                    api_key = line.split(':')[1].strip()
                    break
            else:
                raise OSError('Failed to access the API-key of MP database from '
                              'environment variables or ~/.config/.pmgrc.yaml file.')

    # generate user-agent information
    program_info = f"{__prog__}/{__version__}"
    python_info = f"Python/{sys.version.split()[0]}"
    platform_info = f"{platform.system()}/{platform.release()}"
    user_agent = f"{program_info} ({python_info} {platform_info})"

    headers = {
        "accept": "application/json",
        "X-API-KEY": api_key,
        "User-Agent": user_agent,
    }
    return headers

def query_mp(params, timeout=60, batch=200, include_struct=False):
    '''
    Request data from the Materials Project (https://materialsproject.org/) database.

    Parameters
    ----------
    params : dict
        Query parameters.
    timeout : float, optional
        The period (in seconds) to await a server reply. Default is 60.
    batch : int, optional
        The number of entries to retrieve in each API request. Default is 200.
    include_struct : bool, optional
        Whether to include crystal structure details. Default is False.

    Returns
    -------
    list
        Retrieved data.
    '''
    request = partial(fetch_url, timeout=timeout, headers=_get_mp_api_headers())
    url = 'https://api.materialsproject.org/materials/summary/?'
    url += urllib.parse.urlencode(params)

    content_first = request(url)
    ntot = content_first['meta']['total_doc']

    if ntot > batch:
        urls = [f'{url}&_page={i+1}' for i in range(round(ntot//batch))]
        with ThreadPoolExecutor() as executor:
            content_others = list(executor.map(request, urls))
        contents = [content_first,] + content_others
    else:
        contents = [content_first,]

    datas = list()
    for content in contents:
        if content is None:
            continue
        datas.extend(content['data'])

    if include_struct:
        for data in datas:
            structure = data['structure']
            cell = Cell()
            cell.basis = np.array(structure['lattice']['matrix'])
            for site in structure['sites']:
                atom = site['species'][0]['element']
                pos = np.array(site['abc'])
                if atom in cell.sites:
                    cell.sites[atom].append(pos)
                else:
                    cell.sites[atom] = [pos,]
            data['struct'] = cell
    return datas

def get_phases(elements, max_ehull=None, include_struct=False,
               backend='OQMD', timeout=60, batch=200):
    '''
    Query phase data from the online database.

    Parameters
    ----------
    elements : list of str
        List of chemical element symbols.
    max_ehull : float, optional
        Maximum energy hull filter. If not specified (None), filtering is
        disabled.
    include_struct : bool, optional
        Whether to include crystal structure details. Default is False.
    bankend : str, optional
        The bacnend database to query. Currently supported: OQMD, MP.
    timeout : float, optional
        The period (in seconds) to await a server reply. Default is 60.
    batch : int, optional
        The number of entries to retrieve in each API request. Default is 200.

    Returns
    -------
    list
        Retrieved phase data. Each phase is represented as a dictionary with
        the following keys: `name`, `id`, `delta_e`, `ehull`, and `struct`.
        `struct` is a `Cell` object if `include_struct` is True, otherwise
        it is None.
    '''
    if timeout <= 0:
        raise ValueError("Timeout must be greater than 0.")
    
    if batch < 10:
        raise ValueError("Batch size must be 10 or more.")

    query_options = dict(timeout=timeout,
                         batch=batch,
                         include_struct=include_struct)

    if backend.lower() == 'oqmd':
        params = {
            'composition': '-'.join(elements),
            'limit': batch,
            'fields': ','.join([
                'name',
                'entry_id',
                # 'icsd_id',
                # 'formationenergy_id',
                'delta_e',
                'stability',
                'unit_cell',
                'sites',
            ]),
        }
        if max_ehull:
            params['filter'] = f'stability<={max_ehull}'

        phases = list()
        for data in query_oqmd(params, **query_options):
            phase = {
                'name': data['name'],
                'id': 'oqmd-{}'.format(data['entry_id']),
                'delta_e': data['delta_e'],
                'ehull': data['stability'],
                'struct': data.get('struct', None),
            }
            phases.append(phase)
    elif backend.lower() == 'mp':
        combs = []
        for i in range(len(elements)):
            for p in combinations(elements, i+1):
                combs.append('-'.join(p))
        params = {
            'chemsys': ','.join(combs),
            'deprecated': False,
            '_per_page': batch,
            '_fields': ','.join([
                # 'formula_pretty',
                'composition_reduced',
                # 'composition',
                # 'nsites',
                'material_id',
                'structure',
                'formation_energy_per_atom',
                'energy_above_hull',
            ]),
            '_all_fields': False,
        }
        if max_ehull:
            params['energy_above_hull_max'] = max_ehull

        phases = list()
        for data in query_mp(params, **query_options):
            compos = data['composition_reduced']
            phase = {
                'name': ''.join([f"{k}{compos[k]:g}" for k in elements if k in compos]),
                'id': data['material_id'],
                'delta_e': data['formation_energy_per_atom'],
                'ehull': data['energy_above_hull'],
                'struct': data.get('struct', None),
            }
            phases.append(phase)
    else:
        raise RuntimeError(f"Unknown backend: {backend} (Supported: OQMD, MP)")

    return phases
