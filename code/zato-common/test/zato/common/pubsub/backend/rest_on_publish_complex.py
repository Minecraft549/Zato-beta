# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# Must come first
from gevent import monkey;
_ = monkey.patch_all()

# stdlib
import warnings
from unittest import main, TestCase
from base64 import b64encode
from json import dumps
from io import BytesIO

# Zato
from zato.common.pubsub.backend.rest_backend import RESTBackend
from zato.common.pubsub.server.rest_publish import PubSubRESTServerPublish
from zato.common.pubsub.models import APIResponse
from zato.broker.client import BrokerClient

# ################################################################################################################################
# ################################################################################################################################

class RESTOnPublishComplexTestCase(TestCase):

    def setUp(self):

        # Suppress ResourceWarnings from gevent
        warnings.filterwarnings('ignore', category=ResourceWarning)

        self.broker_client = BrokerClient()
        self.rest_server = PubSubRESTServerPublish('localhost', 8080, should_init_broker_client=False)
        self.rest_server.backend = RESTBackend(self.rest_server, self.broker_client)

        # Test data constants
        self.test_cid = 'test-cid-123'
        self.test_username = 'test_user'
        self.test_password = 'secure_password_123'
        self.test_topic = 'test.topic'

        # Add test user to server
        self.rest_server.users[self.test_username] = {'sec_name': 'test_sec_def', 'password': self.test_password}

        # Add permissions for test user
        self.rest_server.backend.pattern_matcher.add_client(self.test_username, [
            {'pattern': 'test.*', 'access_type': 'publisher'}
        ])

# ################################################################################################################################

    def _create_basic_auth_header(self, username, password):
        credentials = f'{username}:{password}'
        encoded = b64encode(credentials.encode('utf-8')).decode('ascii')
        return f'Basic {encoded}'

    def _create_environ(self, auth_header, data=None):
        json_data = dumps(data) if data else '{}'
        environ = {
            'HTTP_AUTHORIZATION': auth_header,
            'wsgi.input': BytesIO(json_data.encode('utf-8')),
            'CONTENT_LENGTH': str(len(json_data)),
            'PATH_INFO': '/api/v1/pubsub/publish'
        }
        return environ

    def _create_start_response(self):
        def start_response(status, headers):
            pass
        return start_response

# ################################################################################################################################

    def test_on_publish_with_complex_data(self):

        # Create valid auth header
        auth_header = self._create_basic_auth_header(self.test_username, self.test_password)

        # Create complex message data
        complex_data = {
            'user_id': 12345,
            'action': 'user_login',
            'metadata': {
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0',
                'timestamp': '2025-01-01T12:00:00Z'
            },
            'items': [
                {'id': 1, 'name': 'Item 1'},
                {'id': 2, 'name': 'Item 2'}
            ]
        }

        message_data = {
            'data': complex_data,
            'priority': 8,
            'expiration': 7200
        }

        environ = self._create_environ(auth_header, data=message_data)
        start_response = self._create_start_response()

        # Call the method under test
        result = self.rest_server.on_publish(self.test_cid, environ, start_response, self.test_topic)

        # Assert response is correct type and successful
        self.assertIsInstance(result, APIResponse)
        self.assertTrue(result.is_ok)
        self.assertEqual(result.cid, self.test_cid)

# ################################################################################################################################

    def test_on_publish_with_list_data(self):

        # Create valid auth header
        auth_header = self._create_basic_auth_header(self.test_username, self.test_password)

        # Create message with list data
        list_data = [
            {'name': 'Alpha', 'value': 100},
            {'name': 'Beta', 'value': 200},
            {'name': 'Gamma', 'value': 300}
        ]

        message_data = {
            'data': list_data
        }

        environ = self._create_environ(auth_header, data=message_data)
        start_response = self._create_start_response()

        # Call the method under test
        result = self.rest_server.on_publish(self.test_cid, environ, start_response, self.test_topic)

        # Assert response is correct type and successful
        self.assertIsInstance(result, APIResponse)
        self.assertTrue(result.is_ok)
        self.assertEqual(result.cid, self.test_cid)

# ################################################################################################################################

    def test_on_publish_with_unicode_data(self):

        # Create valid auth header
        auth_header = self._create_basic_auth_header(self.test_username, self.test_password)

        # Create message with Greek Unicode characters
        unicode_data = {
            'greeting': 'Γεια σας',
            'message': 'Αυτό είναι ένα μήνυμα δοκιμής',
            'symbols': 'αβγδεζηθικλμνξοπρστυφχψω'
        }

        message_data = {
            'data': unicode_data
        }

        environ = self._create_environ(auth_header, data=message_data)
        start_response = self._create_start_response()

        # Call the method under test
        result = self.rest_server.on_publish(self.test_cid, environ, start_response, self.test_topic)

        # Assert response is correct type and successful
        self.assertIsInstance(result, APIResponse)
        self.assertTrue(result.is_ok)
        self.assertEqual(result.cid, self.test_cid)

# ################################################################################################################################

    def test_on_publish_with_empty_dict_data(self):

        # Create valid auth header
        auth_header = self._create_basic_auth_header(self.test_username, self.test_password)

        # Create message with empty dictionary
        message_data = {
            'data': {}
        }

        environ = self._create_environ(auth_header, data=message_data)
        start_response = self._create_start_response()

        # Call the method under test
        result = self.rest_server.on_publish(self.test_cid, environ, start_response, self.test_topic)

        # Assert response is correct type and successful
        self.assertIsInstance(result, APIResponse)
        self.assertTrue(result.is_ok)
        self.assertEqual(result.cid, self.test_cid)

# ################################################################################################################################

    def test_on_publish_with_empty_list_data(self):

        # Create valid auth header
        auth_header = self._create_basic_auth_header(self.test_username, self.test_password)

        # Create message with empty list
        message_data = {
            'data': []
        }

        environ = self._create_environ(auth_header, data=message_data)
        start_response = self._create_start_response()

        # Call the method under test
        result = self.rest_server.on_publish(self.test_cid, environ, start_response, self.test_topic)

        # Assert response is correct type and successful
        self.assertIsInstance(result, APIResponse)
        self.assertTrue(result.is_ok)
        self.assertEqual(result.cid, self.test_cid)

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':
    _ = main()

# ################################################################################################################################
# ################################################################################################################################
