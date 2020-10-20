from .ensemblclient import EnsemblClient, _api_table
from .core import HTTPError, InvalidResponseError, _endpoint_docstring
from .assemblymapper import AssemblyMapper
from .utils import region_str

_default_client = EnsemblClient()

for endpoint in _api_table:
    docstring = _endpoint_docstring(endpoint)
    exec(f"def {endpoint['name']}(*args, **kwargs):                 \n"
         f"    '''                                                  \n"
         f"    {docstring}                                          \n"
         f"    '''                                                  \n"
         f"    return _default_client.{endpoint['name']}(*args, **kwargs)"
    )