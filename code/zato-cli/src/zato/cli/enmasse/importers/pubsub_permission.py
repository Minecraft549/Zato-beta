# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import logging

# Zato
from zato.common.api import PubSub
from zato.common.odb.model import PubSubPermission, SecurityBase
from zato.common.odb.query import pubsub_permission_list
from zato.common.util.sql import set_instance_opaque_attrs

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from zato.common.typing_ import any_, anydict, stranydict
    from sqlalchemy.orm.session import Session as SASession
    any_ = any_
    anydict = anydict
    stranydict = stranydict
    SASession = SASession

# ################################################################################################################################
# ################################################################################################################################

logger = logging.getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

class PubSubPermissionImporter:
    """ Handles importing pub/sub permission definitions from YAML configuration files.
    """

    def __init__(self, importer:'any_') -> 'None':
        self.importer = importer
        self.pubsub_permission_defs = {}

# ################################################################################################################################

    def _process_pubsub_permission_defs(self, query_result:'any_', out:'dict') -> 'None':
        """ Process pub/sub permission definitions from database query result.
        """
        logger.info('Processing pub/sub permission definitions from database')

        items = list(query_result)
        search_result = items[0]
        items = search_result.result

        logger.info('Processing %d pub/sub permission definitions', len(search_result.result))

        for item in items:

            # Each item is a tuple: (PubSubPermission, security_name, subscription_count)
            permission_obj = item[0]  # First element is the PubSubPermission object
            security_name = item[1]   # Second element is the security name
            subscription_count = item[2]  # Third element is the subscription count

            if hasattr(permission_obj, '_asdict'):
                permission_obj = permission_obj._asdict()
                permission_obj = permission_obj['PubSubPermission']

            # Extract fields directly from the permission object
            permission_dict = {
                'id': permission_obj.id,
                'sec_base_id': permission_obj.sec_base_id,
                'pattern': permission_obj.pattern,
                'access_type': permission_obj.access_type,
                'is_active': permission_obj.is_active,
                'cluster_id': permission_obj.cluster_id
            }

            # Add additional fields from the query
            permission_dict['security_name'] = security_name
            permission_dict['subscription_count'] = subscription_count

            # Create a unique key for this permission
            key = f"{permission_dict['sec_base_id']}_{permission_dict['pattern']}_{permission_dict['access_type']}"
            logger.info('Processing pub/sub permission definition: %s (id=%s) security_name=%s', key, permission_dict.get('id'), security_name)
            out[key] = permission_dict

# ################################################################################################################################

    def get_pubsub_permission_defs_from_db(self, session:'SASession', cluster_id:'int') -> 'anydict':
        out = {}

        logger.info('Retrieving pub/sub permission definitions from database for cluster_id=%s', cluster_id)
        permissions = pubsub_permission_list(session, cluster_id)

        self._process_pubsub_permission_defs(permissions, out)
        logger.info('Total pub/sub permission definitions from DB: %d', len(out))

        for key in out:
            logger.info('DB pub/sub permission def: key=%s', key)

        return out

# ################################################################################################################################

    def create_pubsub_permission_definition(self, definition:'stranydict', session:'SASession') -> 'PubSubPermission':
        """ Creates a new pub/sub permission definition in the database.
        """
        logger.info('Creating pub/sub permission definition: %s', definition)

        instance = PubSubPermission()
        instance.cluster_id = definition.get('cluster_id', 1)
        instance.sec_base_id = definition['sec_base_id']
        instance.pattern = definition['pattern']
        instance.access_type = definition['access_type']
        instance.is_active = definition.get('is_active', True)

        set_instance_opaque_attrs(instance, definition)
        session.add(instance)
        session.commit()

        return instance

# ################################################################################################################################

    def update_pubsub_permission_definition(self, definition:'stranydict', session:'SASession') -> 'PubSubPermission':
        """ Updates an existing pub/sub permission definition in the database.
        """
        logger.info('Updating pub/sub permission definition: %s', definition)

        instance = session.query(PubSubPermission).filter_by(id=definition['id']).one()
        instance.sec_base_id = definition['sec_base_id']
        instance.pattern = definition['pattern']
        instance.access_type = definition['access_type']
        instance.is_active = definition.get('is_active', True)

        set_instance_opaque_attrs(instance, definition)
        session.commit()

        return instance

# ################################################################################################################################

    def should_create_pubsub_permission_definition(self, yaml_def:'stranydict', db_defs:'anydict') -> 'bool':
        """ Determines if a pub/sub permission definition should be created.
        """
        key = f"{yaml_def['sec_base_id']}_{yaml_def['pattern']}_{yaml_def['access_type']}"
        return key not in db_defs

# ################################################################################################################################

    def should_update_pubsub_permission_definition(self, yaml_def:'stranydict', db_def:'stranydict') -> 'bool':
        """ Determines if a pub/sub permission definition should be updated by comparing YAML and DB definitions.
        Always returns True to ensure existing permissions are updated on subsequent syncs.
        """
        # Always update existing permissions to refresh timestamps and ensure consistency
        return True

# ################################################################################################################################

    def get_security_base_id_by_name(self, security_name:'str', session:'SASession') -> 'int':
        """ Gets the security base ID by name.
        """
        sec_base = session.query(SecurityBase).filter_by(name=security_name, cluster_id=self.importer.cluster_id).one()
        return sec_base.id

# ################################################################################################################################

    def sync_pubsub_permission_definitions(self, permission_list:'list', session:'SASession') -> 'tuple':
        """ Synchronizes pub/sub permission definitions from YAML with the database.
        """
        logger.info('Processing %d pub/sub permission definitions from YAML', len(permission_list))

        # Get existing definitions from database
        db_defs = self.get_pubsub_permission_defs_from_db(session, self.importer.cluster_id)

        created = []
        updated = []

        for yaml_def in permission_list:
            security_name = yaml_def['security']
            logger.info('Processing YAML pub/sub permission definition for security: %s', security_name)

            # Get security base ID
            sec_base_id = self.get_security_base_id_by_name(security_name, session)

            # Collect all patterns for each access type
            pub_patterns = yaml_def.get('pub', [])
            sub_patterns = yaml_def.get('sub', [])

            # Create single permission with combined patterns and publisher-subscriber access type
            if pub_patterns or sub_patterns:
                combined_patterns = []

                # Add pub patterns with prefix
                for pattern in pub_patterns:
                    combined_patterns.append(f"pub={pattern}")

                # Add sub patterns with prefix
                for pattern in sub_patterns:
                    combined_patterns.append(f"sub={pattern}")

                combined_pattern = '\n'.join(combined_patterns)
                permission_def = {
                    'sec_base_id': sec_base_id,
                    'pattern': combined_pattern,
                    'access_type': PubSub.API_Client.Publisher_Subscriber,
                    'is_active': yaml_def.get('is_active', True),
                    'cluster_id': 1
                }

                key = f"{sec_base_id}_{combined_pattern}_{PubSub.API_Client.Publisher_Subscriber}"
                logger.info('DEBUG: Publisher_Subscriber constant value: %s', PubSub.API_Client.Publisher_Subscriber)
                logger.info('DEBUG: Checking if should create permission with key: %s', key)
                logger.info('DEBUG: Key exists in db_defs: %s', key in db_defs)
                if key in db_defs:
                    logger.info('DEBUG: Existing permission found: %s', db_defs[key])

                if self.should_create_pubsub_permission_definition(permission_def, db_defs):
                    instance = self.create_pubsub_permission_definition(permission_def, session)
                    created.append(instance)
                    self.pubsub_permission_defs[key] = {
                        'id': instance.id,
                        'sec_base_id': instance.sec_base_id,
                        'pattern': instance.pattern,
                        'access_type': instance.access_type,
                        'is_active': instance.is_active,
                        'cluster_id': instance.cluster_id
                    }
                else:
                    permission_def['id'] = db_defs[key]['id']
                    instance = self.update_pubsub_permission_definition(permission_def, session)
                    updated.append(instance)
                    self.pubsub_permission_defs[key] = {
                        'id': instance.id,
                        'sec_base_id': instance.sec_base_id,
                        'pattern': instance.pattern,
                        'access_type': instance.access_type,
                        'is_active': instance.is_active,
                        'cluster_id': instance.cluster_id
                    }

        logger.info('pub/sub permission definitions sync completed: created=%d, updated=%d', len(created), len(updated))
        return created, updated

# ################################################################################################################################
# ################################################################################################################################
