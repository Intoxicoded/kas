# kas - setup tool for bitbake based projects
#
# Copyright (c) Siemens AG, 2017-2020
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
    This module loads external extensions
'''
__license__ = 'MIT'
__copyright__ = 'Copyright (c) Siemens AG, 2017-2024'

import importlib.metadata
import os
import logging
import json

from . import CONFIGSCHEMA
from .kasusererror import KasUserError

def _load_extensions():
    """
        Loads external plugins and schema extensions

        Using additionalProperties doesn't seem appropriate if extending the schema
        with custom but equally strict additions, this shall provide more clarity
        and feedback utilizing python extensions
    """
    global KAS_EXTENDED_PLUGINS
    global KAS_EXTENDED_SCHEMA

    KAS_EXTENDED_PLUGINS = {}
    KAS_EXTENDED_SCHEMA = {}

    if os.environ.get('KAS_EXTERNAL_PLUGINS', '0') != '1':
        return
    
    ep = importlib.metadata.entry_points()

    # This might be an older version of python, if it has get use that
    entry_points = ep.get('kas.plugins') if hasattr(ep, 'get') else ep.select(group='kas.plugins')
    for entry_point in entry_points:
        if entry_point.name in KAS_EXTENDED_SCHEMA or entry_point.name in KAS_EXTENDED_PLUGINS:
            raise KasUserError(f"Duplicate extension found {entry_point.name}")
        
        ext = entry_point.load()

        if hasattr(ext, '__KAS_PLUGINS__'):
            KAS_EXTENDED_PLUGINS[entry_point.name] = ext
        
        ext_schema = getattr(ext, '__KAS_SCHEMA__')
        if ext_schema:
            print(f'found schmea for {entry_point.name}')
            KAS_EXTENDED_SCHEMA[entry_point.name] = ext_schema()

_load_extensions()

# TODO probably can include signature checking

def verify_extensions():
    # verify the loaded plugins are valid
    extension_conflicts = False
    
    plugins = {}
    for name, plugin in KAS_EXTENDED_PLUGINS.items():
        for plugin in getattr(plugin, "__KAS_PLUGINS__", {}):
            if plugin in plugins:
                logging.error(F'Plugin {name}:{plugin} conflics with {plugins[plugin]}:plugin')
                extension_conflicts = True
            
            plugins[plugin] = name

            missing = []
            if not hasattr(plugin, 'name'):
                missing += ['name']
            if not hasattr(plugin, 'helpmsg'):
                missing += ['helpmsg']
            if not hasattr(plugin, 'setup_parser'):
                missing += ['setup_parser']
            if not hasattr(plugin, 'run'):
                missing += ['run']
            
            if missing:
                logging.error(f"External plugin '{name}' missing {missing}")
                extension_conflicts = True
                
    for name, ext_schema in KAS_EXTENDED_SCHEMA.items():
        missing = []
        if not hasattr(ext_schema, 'root_properties'):
            missing += ['root_properties']
        if not hasattr(ext_schema, 'validate'):
            missing += ['validate']

        if missing:
            logging.error(f"External schema '{name}' missing {missing}")
            extension_conflicts = True

        properties_found = set()

        for key in ext_schema.root_properties():
            if key in CONFIGSCHEMA['properties']:
                extension_conflicts = True
                logging.error(
                    f'Schema extension {name} conflicts with property {key}\n')
                
            elif key in properties_found:
                extension_conflicts = True
                logging.error(
                    f'Schema extension {name} conflicts extended property {key}\n')

            properties_found.add(key)


    if extension_conflicts:
        raise KasUserError("Found errors in user extensions")
