"""

This file is part of pyEnsemblRest.
    Copyright (C) 2018, Andrés García

    Any questions, comments or issues can be addressed to a.garcia230395@gmail.com.

"""

import json
from importlib_resources import open_text, path
from .core import build_client_class

# Import API information
with open_text('ensembl_rest.data','ensembl_rest_endpoints.json') as f:
    _api_table = json.load(f)


# Now create the main classes 
ensembl_rest_url = 'https://rest.ensembl.org'

EnsemblClient = build_client_class(
                'EnsemblClient', 
                _api_table,
                base_url=ensembl_rest_url,
                doc=f'A client for the Ensembl REST API ({ensembl_rest_url})')