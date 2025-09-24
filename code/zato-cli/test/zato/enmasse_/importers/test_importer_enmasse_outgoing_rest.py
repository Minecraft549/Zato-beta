# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import os
import tempfile
from unittest import TestCase, main

# Zato
from zato.cli.enmasse.client import cleanup_enmasse, get_session_from_server_dir
from zato.cli.enmasse.importer import EnmasseYAMLImporter
from zato.cli.enmasse.importers.outgoing_rest import OutgoingRESTImporter
from zato.cli.enmasse.importers.security import SecurityImporter
from zato.common.api import CONNECTION, URL_TYPE
from zato.common.odb.model import HTTPSOAP
from zato.common.test.enmasse_._template_complex_01 import template_complex_01
from zato.common.typing_ import cast_

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from zato.common.typing_ import any_, stranydict
    any_, stranydict = any_, stranydict

# ################################################################################################################################
# ################################################################################################################################

class TestEnmasseOutgoingRESTFromYAML(TestCase):
    """ Tests importing outgoing REST connections from YAML files using enmasse.
    """

    def setUp(self) -> 'None':
        # Server path for database connection
        self.server_path = os.path.expanduser('~/env/qs-1/server1')

        # Create a temporary file using the existing template which already contains outgoing REST connections
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
        _ = self.temp_file.write(template_complex_01.encode('utf-8'))
        self.temp_file.close()

        # Initialize the importer
        self.importer = EnmasseYAMLImporter()

        # Initialize security importer (needed for outgoing connections with security)
        self.security_importer = SecurityImporter(self.importer)
        self.importer.sec_defs = {} # Initialize sec_defs

        # Initialize outgoing REST importer
        self.outgoing_rest_importer = OutgoingRESTImporter(self.importer)

        # Parse the YAML file
        self.yaml_config = cast_('stranydict', None)
        self.session = cast_('any_', None)

# ################################################################################################################################

    def tearDown(self) -> 'None':
        if self.session:
            self.session.close()
        os.unlink(self.temp_file.name)
        cleanup_enmasse()

# ################################################################################################################################

    def _setup_test_environment(self):
        """ Set up the test environment by opening a database session and parsing the YAML file.
        """
        if not self.session:
            self.session = get_session_from_server_dir(self.server_path, stdin_data='')

        if not self.yaml_config:
            self.yaml_config = self.importer.from_path(self.temp_file.name)

        # Create security definitions first since outgoing REST connections may use them
        security_list = self.yaml_config['security']
        _ = self.security_importer.sync_security_definitions(security_list, self.session)
        self.session.commit()

        # Security definitions are already populated in self.importer.sec_defs by the security importer

# ################################################################################################################################

    def test_outgoing_rest_creation(self):
        """ Test creating outgoing REST connections from YAML.
        """
        self._setup_test_environment()

        # Get outgoing REST definitions from YAML
        outgoing_rest_defs = self.yaml_config['outgoing_rest']

        # Process all outgoing REST definitions
        created, updated = self.outgoing_rest_importer.sync_outgoing_rest(outgoing_rest_defs, self.session)

        # Should have created all 5 connections
        self.assertEqual(len(created), 5)
        self.assertEqual(len(updated), 0)

        # Verify the first outgoing REST connection was created correctly
        outgoing = self.session.query(HTTPSOAP).filter_by(
            name='enmasse.outgoing.rest.1',
            connection=CONNECTION.OUTGOING,
            transport=URL_TYPE.PLAIN_HTTP
        ).one()

        self.assertEqual(outgoing.host, 'https://example.com:443')
        self.assertEqual(outgoing.url_path, '/sso/{{type}}/hello/{{endpoint}}')
        self.assertEqual(outgoing.data_format, 'json')
        self.assertEqual(outgoing.timeout, 60)

# ################################################################################################################################

    def test_outgoing_rest_update(self):
        """ Test updating existing outgoing REST connections.
        """
        self._setup_test_environment()

        # First, get an outgoing REST definition from YAML and create it
        outgoing_rest_defs = self.yaml_config['outgoing_rest']
        # Use a definition without security to avoid complications
        outgoing_def = next(item for item in outgoing_rest_defs if 'security' not in item)

        # Create the outgoing REST connection
        instance = self.outgoing_rest_importer.create_outgoing_rest(outgoing_def, self.session)
        self.session.commit()
        original_host = outgoing_def['host']
        self.assertEqual(instance.host, original_host)

        # Prepare an update definition based on the existing one
        update_def = {
            'name': outgoing_def['name'],
            'id': instance.id,
            'host': 'https://updated-example.com',  # Changed host
            'url_path': '/updated/path',  # Changed path
            'timeout': 30  # Changed timeout
        }

        # Update the outgoing REST connection
        updated_instance = self.outgoing_rest_importer.update_outgoing_rest(update_def, self.session)
        self.session.commit()

        # Verify the update was applied
        self.assertEqual(updated_instance.host, 'https://updated-example.com')
        self.assertEqual(updated_instance.url_path, '/updated/path')
        self.assertEqual(updated_instance.timeout, 30)

        # Make sure other fields were preserved
        self.assertEqual(updated_instance.connection, CONNECTION.OUTGOING)
        self.assertEqual(updated_instance.transport, URL_TYPE.PLAIN_HTTP)

# ################################################################################################################################w

    def test_complete_outgoing_rest_import_flow(self):
        """ Test the complete flow of importing outgoing REST connections from a YAML file.
        """
        self._setup_test_environment()

        # Process all outgoing REST definitions from the YAML
        outgoing_rest_list = self.yaml_config['outgoing_rest']
        outgoing_created, outgoing_updated = self.outgoing_rest_importer.sync_outgoing_rest(outgoing_rest_list, self.session)

        # Update main importer's outgoing REST definitions
        self.importer.outgoing_rest_defs = self.outgoing_rest_importer.connection_defs

        # Verify outgoing REST connections were created
        count = len(outgoing_rest_list)
        self.assertEqual(len(outgoing_created), count)
        self.assertEqual(len(outgoing_updated), 0)

        # Verify the outgoing REST connections dictionary was populated
        enmasse_connections = {name: conn for name, conn in self.outgoing_rest_importer.connection_defs.items() if name.startswith('enmasse')}
        self.assertEqual(len(enmasse_connections), count)

        # Verify that these definitions are accessible from the main importer
        enmasse_defs_in_importer = {name: conn for name, conn in self.importer.outgoing_rest_defs.items() if name.startswith('enmasse')}
        self.assertEqual(len(enmasse_defs_in_importer), count)

# ################################################################################################################################

    def test_outgoing_rest_configuration(self):
        """ Test the configuration of outgoing REST connections.
        """
        self._setup_test_environment()

        # Verify outgoing_rest configurations exist in the YAML
        outgoing_defs = self.yaml_config['outgoing_rest']
        self.assertTrue(len(outgoing_defs) > 0, 'No outgoing REST definitions found in YAML')

        # Check specific properties in the outgoing connections
        for item in outgoing_defs:
            self.assertIn('name', item)
            self.assertIn('host', item)
            self.assertIn('url_path', item)
            self.assertTrue(item['name'].startswith('enmasse.outgoing.rest.'))

        # Verify the specific details for each connection
        conn1 = cast_('any_', None)
        conn2 = cast_('any_', None)
        conn5 = cast_('any_', None)

        # Find connections by name using a simple loop
        for item in outgoing_defs:
            if item['name'] == 'enmasse.outgoing.rest.1':
                conn1 = item
            elif item['name'] == 'enmasse.outgoing.rest.2':
                conn2 = item
            elif item['name'] == 'enmasse.outgoing.rest.5':
                conn5 = item

        # Check conn1 details
        self.assertIsNotNone(conn1)
        self.assertEqual(conn1['host'], 'https://example.com:443')
        self.assertEqual(conn1['url_path'], '/sso/{{type}}/hello/{{endpoint}}')
        self.assertEqual(conn1['data_format'], 'json')
        self.assertEqual(conn1['timeout'], 60)

        # Check conn2 security configuration
        self.assertIsNotNone(conn2)
        self.assertIn('security', conn2)
        self.assertEqual(conn2['security'], 'enmasse.bearer_token.1')

        # Check conn5 TLS verification setting
        self.assertIsNotNone(conn5)
        self.assertIn('tls_verify', conn5)
        self.assertEqual(conn5['tls_verify'], False)

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':

    # stdlib
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    _ = main()

# ################################################################################################################################
# ################################################################################################################################
