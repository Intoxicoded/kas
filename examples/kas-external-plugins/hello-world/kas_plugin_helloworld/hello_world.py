# kas - setup tool for bitbake based projects
#
# Copyright (c) Siemens AG, 2025
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Example to show how to write external kas plugins
"""

__license__ = 'MIT'
__copyright__ = 'Copyright (c) Siemens AG, 2025'

import yaml

from jsonschema.validators import validator_for

from kas.context import get_context
from kas.plugins.checkout import Checkout

import logging

logger = logging.Logger(__name__)

SCHEMA = yaml.safe_load('''
$schema: http://json-schema.org/draft-04/schema#
$id: hello-data
type: object
title: hello world extended data
description: example
required: []
additionalProperties: false
properties:
  hello-data:
    type: object
    description:
    required:
      - message
    properties:
      message:
        type: string
''')

EXT_VALIDATOR_CLASS = validator_for(SCHEMA)
EXT_VALIDATOR = EXT_VALIDATOR_CLASS(SCHEMA)

class HelloWorldSchema:
    """
        This implements a custom schema loader for extending data when using a kas plugin. 

            - root_properties
    """

    @classmethod
    def root_properties(cls):
        props = SCHEMA.get('properties', {}).keys()
        return props
    
    @classmethod
    def validate(cls, data):
        validated = True
        # validate the extended properties with the schema
        for error in sorted(EXT_VALIDATOR.iter_errors(data), key=str):
            logger.error('Ex:\n%s', error.message)
            validated = False
        return validated

class HelloWorld(Checkout):
    """
        This plugin implements the ``kas hello-world`` command.
        When this command is executed, kas will print a hello world message.
        The following is the bare-minimum required to implement a kas plugin:
            - name: Name of the sub command to run the plugin
            - helpmsg: Help message that is displayed when the user runs ``kas -h``.
            - setup_parser: Setup the sub-parser of this plugin.
            - run: Method that is called when executing the plugin.

        An additional schema object can be provided by implementing 
            - load_schema: Object that is used to define additional properties
    """
    name = 'hello-world'
    helpmsg = (
        'Prints a hello world message'
    )

    @classmethod
    def setup_parser(self, parser):
        super().setup_parser(parser)

    def run(self, args):
        args.skip += [
            'setup_dir',
            'repos_apply_patches',
            'setup_environ',
            'write_bbconfig',
        ]

        super().run(args)
        ctx = get_context()
        config = ctx.config.get_ext_config()
        data = config.get('hello-data', {})
        message = data.get('message')
        if message:
            print(f'Hello, {message}')
        else:
            print("No message found!")
