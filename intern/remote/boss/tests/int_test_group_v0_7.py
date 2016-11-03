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
from intern.remote.boss import BossRemote
import random

import requests
from requests import Session, HTTPError, Request
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import unittest
import warnings

API_VER = 'v0.7'


class ProjectGroupTest_v0_7(unittest.TestCase):
    """Integration tests of the Boss group API.
    """

    @classmethod
    def setUpClass(cls):
        """Do an initial DB clean up in case something went wrong the last time.

        If a test failed really badly, the DB might be in a bad state despite
        attempts to clean up during tearDown().
        """
        warnings.filterwarnings('ignore')
        cls.rmt = BossRemote('test.cfg', API_VER)

        # Turn off SSL cert verification.  This is necessary for interacting with
        # developer instances of the Boss.
        cls.rmt.project_service.session_send_opts = {'verify': False}
        cls.rmt.metadata_service.session_send_opts = {'verify': False}
        cls.rmt.volume_service.session_send_opts = {'verify': False}
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        cls.create_grp_name = 'int_test_group{}'.format(random.randint(0, 9999))
        cls.existing_grp_name = 'int_test_group_exists{}'.format(random.randint(0, 9999))
        cls.user_name = 'bossadmin'

        # This user will be created during at least one test.
        cls.create_user = 'group_test_johndoeski{}'.format(random.randint(0, 9999))

        cls.rmt.create_group(cls.existing_grp_name)


    @classmethod
    def tearDownClass(cls):
        """Clean up the data model objects used by this test case.

        This method is used by both tearDown() and setUpClass().  Don't do
        anything if an exception occurs during delete_group().  The group
        may not have existed for a particular test.
        """
        try:
            cls.rmt.delete_group(cls.create_grp_name)
        except HTTPError:
            pass
        try:
            cls.rmt.delete_group(cls.existing_grp_name)
        except HTTPError:
            pass
        try:
            cls.rmt.delete_user(cls.create_user)
        except HTTPError:
            pass

    def tearDown(self):
        #try:
        #    self.rmt.delete_group(self.create_grp_name)
        #except HTTPError:
        #    pass
        pass

    def test_create_group(self):
        self.rmt.create_group(self.create_grp_name)

    def test_get_group(self):
        actual = self.rmt.get_group(self.existing_grp_name)
        self.assertTrue(actual)

    def test_get_group_doesnt_exist(self):
        actual = self.rmt.get_group('foo')
        self.assertFalse(actual)

    def test_delete_group(self):
        actual = self.rmt.get_group(self.existing_grp_name)
        self.assertTrue(actual)

        self.rmt.delete_group(self.existing_grp_name)
        actual = self.rmt.get_group(self.existing_grp_name)
        self.assertFalse(actual)

        self.rmt.create_group(self.existing_grp_name)
        actual = self.rmt.get_group(self.existing_grp_name)
        self.assertTrue(actual)

    def test_delete_group_doesnt_exist(self):
        with self.assertRaises(HTTPError):
            self.rmt.delete_group('foo')

    def test_add_user_to_group(self):
        self.rmt.add_user_to_group(self.existing_grp_name, self.user_name)

    def test_add_user_to_group_group_doesnt_exist(self):
        with self.assertRaises(HTTPError):
            self.rmt.add_user_to_group('foo', self.user_name)

    def test_group_membership(self):
        # Test not in the group
        self.assertFalse(self.rmt.get_group(self.existing_grp_name, self.user_name))

        # Add to group
        self.rmt.add_user_to_group(self.existing_grp_name, self.user_name)
        self.assertTrue(self.rmt.get_group(self.existing_grp_name, self.user_name))

    def test_get_group_user_doesnt_exist(self):
        with self.assertRaises(HTTPError):
            self.rmt.get_group(self.existing_grp_name, 'foo')

    def test_delete_group_user(self):
        self.rmt.delete_group(self.existing_grp_name, self.user_name)

    def test_delete_group_user_doesnt_exist(self):
        with self.assertRaises(HTTPError):
            self.rmt.delete_group(self.existing_grp_name, 'foo')

    def test_get_groups(self):
        password = 'myPassW0rd'
        self.rmt.add_user(
            self.create_user, 'John', 'Doeski', 'jdoe@me.com', password)
        token = self.get_access_token(self.create_user, password)
        self.login_user(token)

        self.rmt.add_user_to_group(self.existing_grp_name, self.create_user)

        # Name of auto-created group for user.
        users_group = self.create_user + '-primary'

        expected = ['bosspublic', users_group, self.existing_grp_name]
        actual = self.rmt.get_user_groups(self.create_user)
        six.assertCountEqual(self, expected, actual)

    def test_get_groups_invalid_user(self):
        with self.assertRaises(HTTPError):
            self.rmt.get_user_groups('foo')

    def login_user(self, token):
        """User must login once before user can be added to a group.

        Args:
            token (string): Bearer token used to for authentication.
        """
        if "Project Service" in self.rmt._config.sections():
            host = self.rmt._config.get("Project Service", "host")
            protocol = self.rmt._config.get("Project Service", "protocol")
        else:
            host = self.rmt._config.get("Default", "host")
            protocol = self.rmt._config.get("Default", "protocol")

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + token
        }

        # Hit one of the API endpoints to effectively, login.
        url = protocol + '://' + host + '/' + API_VER + '/collection/'
        session = Session()
        request = Request('GET', url, headers=headers)
        prep = session.prepare_request(request)
        response = session.send(prep, verify=False)

    def get_access_token(self, user_name, password):
        """Get the bearer token for the test user for login.

        Will assert or raise on a failure.

        Returns:
            (string): Bearer token.
        """
        if "Project Service" in self.rmt._config.sections():
            (api_host, domain) = self.rmt._config.get("Project Service", "host").split('.', 1)
            protocol = self.rmt._config.get("Project Service", "protocol")
        else:
            (api_host, domain) = self.rmt._config.get("Default", "host").split('.', 1)
            protocol = self.rmt._config.get("Default", "protocol")

        host = api_host.replace('api', 'auth', 1) + '.' + domain
        url = protocol + '://' + host + '/auth/realms/BOSS/protocol/openid-connect/token'
        data = {
            'grant_type': 'password',
            'client_id': 'endpoint',
            'username': user_name,
            'password': password
            }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        session = Session()
        request = Request('POST', url, data=data, headers=headers)
        prep = session.prepare_request(request)
        response = session.send(prep, verify=False)
        jresp = response.json()
        self.assertIn('access_token', jresp)
        return jresp['access_token']


if __name__ == '__main__':
    unittest.main()