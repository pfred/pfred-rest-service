"""

This file is part of pyEnsembl.
    Copyright (C) 2018, Andrés García

    Any questions, comments or issues can be addressed to a.garcia230395@gmail.com.

"""

from .restclient import RESTClient, HTTPError
import pprint


class BaseEnsemblRESTClient:
    """Base client for an Ensembl REST API."""
    
    def __init__(self, base_url=None):
        if base_url is None:
            base_url = self.base_url
            
        self.rest_client = RESTClient(base_url)
    # ----
        
    def make_request(self, resource, *args, params=None, headers=None, **kwargs):
        "Follow the route mapping the arguments to the correct place."
        # Assemble the request
        request_type, route_template = resource.split(' ')
        route = self._map_arguments(route_template, *args, **kwargs)
        
        endpoint = self.rest_client.route(*route)
        
        # Perform the request
        while True:
            try:
                return endpoint.do(request_type, params, headers=headers)

            # Handle rate limit
            except HTTPError as e:
                    if e.response.status_code == 429:
                        # Maximum requests rate exceded
                        # Need to wait
                        response = e.response
                        wait_time = float(response.headers["Retry-After"])
                        sys.stderr.write('Maximum requests limit reached, waiting for ' 
                                         + str(wait_time)
                                         + 'secs')
                        time.sleep(wait_time)
                    else:
                        raise
    # ---        
        
    def _map_arguments(self, route, *args, **kwargs):
        """Map the arguments to the template.
        
        The template is a string of the form:
        "some/:string/with/:semicolons"
        
        First maps the **kwargs, then maps the *args in order.
        If this fails throw an exception.
        
        """
        # First split into arguments: 
        # "some/:string/with/:semicolons" -> ['some', ':string', 'with', ':semicolons'] 
        parts = route.split('/')
        # Then replace the semicolons with format strings
        parts = ['{' + s[1:] + '}' if s.startswith(':') else s for s in parts]
        
        # Then map the keyword arguments
        parts = [self._format_if_possible(s, **kwargs) for s in parts]
        
        # Finally, map the positional arguments
        args_iter = iter(args)
        mapped_parts = []
        for s in parts:
            if s.startswith('{'):
                try:
                    mapped_parts.append(next(args_iter))
                except StopIteration:
                    # Parameter not provided, skip in case it is optional
                    pass
            else:
                mapped_parts.append(s)
        
        return mapped_parts
    # ---
           
    def _format_if_possible(self, format_string, **kwargs):
        """Try to apply the arguments to the format string.
        
        If not possible, return the string unchanged.
        """
        try:
            return format_string.format(**kwargs)
        except KeyError:
            return format_string
    # ---
    
# --- BaseClient




## Now are the factories for the automated creation of the classes
##  Y Y Y Y Y
##  | | | | |
##  v v v v v

def _format_parameters_docstring(parameters):
    fields = 'Type,Description,Default,Example Values'.split(',')

    parameters_str = ''
    for parameter in parameters:
        parameters_str += f'  + *Name*: {parameter["Name"]}\n\n'
        
        for field in fields:
            parameters_str += f'    * *{field}*: {parameter[field]}\n'

        parameters_str += '\n\n'

    return parameters_str
# ---

def _endpoint_docstring(endpoint):
    resource_info = '\n'.join(f'- **{name}**:\t{values}' for name, values in endpoint['resource_info'].items())
    return (
        f"{endpoint['category']} ``{endpoint['resource_string']}``\n\n"
        f"{endpoint['description']}\n\n\n"
        f"**Parameters**\n\n"
        f"- Required:\n\n{_format_parameters_docstring(endpoint['parameters']['required'])}"
        f"- Optional:\n\n{_format_parameters_docstring(endpoint['parameters']['optional'])}"
        f"**Resource info**\n\n"
        f"{resource_info}\n\n\n"
        f"**More info**\n\n"
        f"{endpoint['documentation_url']}\n\n"
    )
# ---

def _create_method(method_name, endpoint):
    """Create a class method"""
    
    def method(self, *args, **kwargs):
        return self.make_request(endpoint['resource_string'], *args, **kwargs)
    # ---
    
    method.__doc__ = _endpoint_docstring(endpoint)
    method.__name__ = method_name
    
    return method
# ---

def build_client_class(name, api_table, base_url, doc=''):
    """Create a new class that implements the methods of the API."""
    # Create the class dictionary
    class_dict = {'__doc__': doc,
                  'base_url': base_url}
    
    # Create the class methods
    methods = {endpoint['name'] : _create_method(endpoint['name'], endpoint) 
               for endpoint in api_table}
    
    class_dict.update(methods)
    
    # Create the class (a subclass of the BaseEnsemblRESTClient)
    return type(name, (BaseEnsemblRESTClient,), class_dict)
# ---
