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


import re
import json
import urllib.request
import urllib.parse
import urllib.error
from functools import partial
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
        The bacnend database to query. Currently supported: OQMD.
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
                'id': data['entry_id'],
                'delta_e': data['delta_e'],
                'ehull': data['stability'],
                'struct': data.get('struct', None),
            }
            phases.append(phase)
    else:
        raise RuntimeError(f"Unknown backend: {backend} (Supported: OQMD)")

    return phases
