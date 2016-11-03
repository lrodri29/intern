﻿# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import six
from abc import ABCMeta
from six.moves import configparser
import os

CONFIG_FILE ='~/.intern/intern.cfg'


@six.add_metaclass(ABCMeta)
class Remote(object):
    """Base class for communicating with remote data stores.

    Attributes:
        _volume (intern.service.Service): Class that communicates with the volume service.
        _metadata (intern.service.Service): Class that communicates with the metadata service.
        _project (intern.service.Service): Class that communicates with the project service.
        _object (intern.service.Service): Class that communicates with the object service.
    """

    def __init__(self, cfg_file_or_dict=None):
        """Constructor.

        Args:
            cfg_file_or_dict (optional[string|dict]): Path to config file in INI format or a dict of config parameters.
        """

        # Service Objects
        self._volume = None
        self._metadata = None
        self._project = None
        self._object = None

        # Configuration data loaded from file or passed directly to the constructor
        # Is available for children Remote classes to use as needed
        self._config = None

        # Tokens for Services
        self._token_project = None
        self._token_metadata = None
        self._token_volume = None
        self._token_object = None

        if cfg_file_or_dict is None:
            # Default to the config file in the user directory if no config file was provided
            cfg_file_or_dict = os.path.expanduser(CONFIG_FILE)

        if isinstance(cfg_file_or_dict, dict) is True:
            # A config dictionary was provided directly. Keep things consistent by creating an INI string.
            cfg_str = "[Default]\n"
            for key in cfg_file_or_dict:
                cfg_str = "{}{} = {}\n".format(cfg_str, key, cfg_file_or_dict[key])
            self._config = self.load_config_file(six.StringIO(cfg_str))

        else:
            # A file path was provided by the user
            if os.path.isfile(cfg_file_or_dict):
                with open(cfg_file_or_dict, 'r') as cfg_file_handle:
                    self._config = self.load_config_file(cfg_file_handle)
            else:
                raise IOError("Configuration file not found: {}".format(cfg_file_or_dict))

    def load_config_file(self, config_handle):
        """Load config data for the Remote.

        Args:
            config_handle (io.StringIO): Config data encoded in a string.

        Returns:
            (configparser.ConfigParser)
        """
        cfg_parser = configparser.ConfigParser()
        cfg_parser.readfp(config_handle)
        return cfg_parser

    @property
    def volume_service(self):
        return self._volume

    @property
    def project_service(self):
        return self._project

    @property
    def metadata_service(self):
        return self._metadata

    @property
    def object_service(self):
        return self._object

    def list_project(self, **kwargs):
        """Perform list operation on the project.

        What this does is highly dependent on project's data model.

        Args:
            (**kwargs): Args are implementation dependent.

        Returns:
            (list)
        """
        return self._project.list(**kwargs)

    def get_cutout(self, resource, resolution, x_range, y_range, z_range, time_range=None):
        """Get a cutout from the volume service.

        Args:
            resource (intern.resource.Resource): Resource compatible with cutout operations.
            resolution (int): 0 indicates native resolution.
            x_range (list[int]): x range such as [10, 20] which means x>=10 and x<20.
            y_range (list[int]): y range such as [10, 20] which means y>=10 and y<20.
            z_range (list[int]): z range such as [10, 20] which means z>=10 and z<20.
            time_range (optional [list[int]]): time range such as [30, 40] which means t>=30 and t<40.

        Returns:
            (): Return type depends on volume service's implementation.

        Raises:
            RuntimeError when given invalid resource.
            Other exceptions may be raised depending on the volume service's implementation.
        """

        if not resource.valid_volume():
            raise RuntimeError('Resource incompatible with the volume service.')
        return self._volume.get_cutout(
            resource, resolution, x_range, y_range, z_range, time_range)

    def create_cutout(self, resource, resolution, x_range, y_range, z_range, data, time_range=None):
        """Upload a cutout to the volume service.

        Args:
            resource (intern.resource.Resource): Resource compatible with cutout operations.
            resolution (int): 0 indicates native resolution.
            x_range (list[int]): x range such as [10, 20] which means x>=10 and x<20.
            y_range (list[int]): y range such as [10, 20] which means y>=10 and y<20.
            z_range (list[int]): z range such as [10, 20] which means z>=10 and z<20.
            data (object): Type depends on implementation.
            time_range (optional [list[int]]): time range such as [30, 40] which means t>=30 and t<40.

        Returns:
            (): Return type depends on volume service's implementation.

        Raises:
            RuntimeError when given invalid resource.
            Other exceptions may be raised depending on the volume service's implementation.
        """
        if not resource.valid_volume():
            raise RuntimeError('Resource incompatible with the volume service.')
        return self._volume.create_cutout(
            resource, resolution, x_range, y_range, z_range, data, time_range)