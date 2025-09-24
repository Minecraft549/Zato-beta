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
from zato.cli.enmasse.importers.scheduler import SchedulerImporter
from zato.common.api import SCHEDULER
from zato.common.odb.model import IntervalBasedJob, Job
from zato.common.test.enmasse_._template_complex_01 import template_complex_01
from zato.common.typing_ import cast_

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from zato.common.typing_ import any_, stranydict
    any_, stranydict = any_, stranydict

# ################################################################################################################################
# ################################################################################################################################

class TestEnmasseSchedulerFromYAML(TestCase):
    """ Tests importing Scheduler definitions from YAML files using enmasse.
    """

    def setUp(self) -> 'None':

        # Server path for database connection
        self.server_path = os.path.expanduser('~/env/qs-1/server1')

        # Create a temporary file using the existing template which already contains scheduler job definitions
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
        _ = self.temp_file.write(template_complex_01.encode('utf-8'))
        self.temp_file.close()

        # Initialize the importer
        self.importer = EnmasseYAMLImporter()

        # Initialize scheduler importer
        self.scheduler_importer = SchedulerImporter(self.importer)

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
            self.session = get_session_from_server_dir(self.server_path)

        if not self.yaml_config:
            self.yaml_config = self.importer.from_path(self.temp_file.name)

# ################################################################################################################################

    def test_job_definition_creation(self):
        """ Test creating scheduler job definitions from YAML.
        """
        self._setup_test_environment()

        # Get definitions from YAML
        job_defs = self.yaml_config['scheduler']

        # Process all scheduler job definitions
        created, updated = self.scheduler_importer.sync_job_definitions(job_defs, self.session)

        # Should have created 4 definitions
        self.assertEqual(len(created), 4)
        self.assertEqual(len(updated), 0)

        # Verify first job was created correctly
        job = self.session.query(Job).filter_by(name='enmasse.scheduler.1').one()
        self.assertEqual(job.job_type, SCHEDULER.JOB_TYPE.INTERVAL_BASED)

        # Verify interval job was created correctly
        interval_job = self.session.query(IntervalBasedJob).filter_by(job_id=job.id).one()
        self.assertEqual(interval_job.seconds, 2)

        # Verify second job was created correctly
        job = self.session.query(Job).filter_by(name='enmasse.scheduler.2').one()
        self.assertEqual(job.job_type, SCHEDULER.JOB_TYPE.INTERVAL_BASED)

        # Verify interval job was created correctly
        interval_job = self.session.query(IntervalBasedJob).filter_by(job_id=job.id).one()
        self.assertEqual(interval_job.minutes, 51)

# ################################################################################################################################

    def test_job_update(self):
        """ Test updating existing scheduler job definitions.
        """
        self._setup_test_environment()

        # First, get the job definition from YAML and create it
        job_defs = self.yaml_config['scheduler']
        job_def = job_defs[0]  # First job has seconds=2

        # Create the job definition
        instance = self.scheduler_importer.create_job_definition(job_def, self.session)
        self.session.commit()
        original_seconds = 2

        # Verify interval job was created with original seconds
        interval_job = self.session.query(IntervalBasedJob).filter_by(job_id=instance.id).one()
        self.assertEqual(interval_job.seconds, original_seconds)

        # Prepare an update definition based on the existing one
        update_def = {
            'name': job_def['name'],
            'id': instance.id,
            'seconds': 5,  # Changed seconds
            'minutes': 30  # Added minutes
        }

        # Update the job definition
        updated_instance = self.scheduler_importer.update_job_definition(update_def, self.session)
        self.session.commit()

        # Verify the interval job was updated
        updated_interval = self.session.query(IntervalBasedJob).filter_by(job_id=updated_instance.id).one()
        self.assertEqual(updated_interval.seconds, 5)
        self.assertEqual(updated_interval.minutes, 30)

# ################################################################################################################################

    def test_complete_job_import_flow(self):
        """ Test the complete flow of importing scheduler job definitions from a YAML file.
        """
        self._setup_test_environment()

        # Process all job definitions from the YAML
        job_list = self.yaml_config['scheduler']
        job_created, job_updated = self.scheduler_importer.sync_job_definitions(job_list, self.session)

        # Update importer's job definitions
        self.importer.job_defs = self.scheduler_importer.job_defs

        # Verify job definitions were created
        self.assertEqual(len(job_created), 4)
        self.assertEqual(len(job_updated), 0)

        # Verify the job definitions dictionary was populated
        self.assertEqual(len(self.scheduler_importer.job_defs), 4)

        # Verify that these definitions are accessible from the main importer
        self.assertEqual(len(self.importer.job_defs), 4)

        # Try importing the same definitions again - should result in updates, not creations
        job_created2, job_updated2 = self.scheduler_importer.sync_job_definitions(job_list, self.session)
        self.assertEqual(len(job_created2), 0)
        self.assertEqual(len(job_updated2), 4)

# ################################################################################################################################

    def test_scheduler_configuration(self):
        """ Test the configuration of scheduled jobs.
        """
        self._setup_test_environment()

        # Verify scheduler configurations exist in the YAML
        scheduler_defs = self.yaml_config['scheduler']
        self.assertTrue(len(scheduler_defs) > 0, 'No scheduler definitions found in YAML')

        # Check common properties for all scheduler items
        for item in scheduler_defs:
            self.assertIn('name', item)
            self.assertIn('service', item)
            self.assertIn('job_type', item)
            self.assertIn('start_date', item)
            self.assertTrue(item['name'].startswith('enmasse.scheduler.'))
            self.assertEqual(item['service'], 'demo.ping')
            self.assertEqual(item['job_type'], 'interval_based')

        # Verify different interval types (seconds, minutes, hours, days)
        scheduler1 = cast_('any_', None)
        scheduler2 = cast_('any_', None)
        scheduler3 = cast_('any_', None)
        scheduler4 = cast_('any_', None)

        # Find scheduler items by name using a simple loop
        for item in scheduler_defs:
            if item['name'] == 'enmasse.scheduler.1':
                scheduler1 = item
            elif item['name'] == 'enmasse.scheduler.2':
                scheduler2 = item
            elif item['name'] == 'enmasse.scheduler.3':
                scheduler3 = item
            elif item['name'] == 'enmasse.scheduler.4':
                scheduler4 = item

        # Check scheduler with seconds interval
        self.assertIsNotNone(scheduler1)
        self.assertIn('seconds', scheduler1)
        self.assertEqual(scheduler1['seconds'], 2)

        # Check scheduler with minutes interval
        self.assertIsNotNone(scheduler2)
        self.assertIn('minutes', scheduler2)
        self.assertEqual(scheduler2['minutes'], 51)

        # Check scheduler with hours interval
        self.assertIsNotNone(scheduler3)
        self.assertIn('hours', scheduler3)
        self.assertEqual(scheduler3['hours'], 3)

        # Check scheduler with days interval
        self.assertIsNotNone(scheduler4)
        self.assertIn('days', scheduler4)
        self.assertEqual(scheduler4['days'], 10)

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':

    # stdlib
    import logging

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    _ = main()

# ################################################################################################################################
# ################################################################################################################################
