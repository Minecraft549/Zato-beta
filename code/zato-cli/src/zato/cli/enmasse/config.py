# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# ################################################################################################################################
# ################################################################################################################################

class _object_type:

    Security = 'security'                         #

    Channel_REST = 'channel_rest'                 #
    Outgoing_REST = 'outgoing_rest'               #
    Outgoing_SOAP = 'outgoing_soap'               #

    Cache = 'cache'                               #

    Odoo = 'odoo'                                 #
    SQL  = 'sql'                                  #
    Scheduler = 'scheduler'                       #

    Email_IMAP = 'email_imap'                     #
    Email_SMTP = 'email_smtp'                     #

    Groups = 'groups'                             #

    LDAP = 'ldap'                                 #
    Confluence = 'confluence'                     #
    Jira = 'jira'                                 #
    Microsoft_365 = 'cloud_microsoft_365'         #
    Search_ElasticSearch = 'elastic_search'       #

    # Channel_AMQP = 'channel_amqp'               #
    # Channel_WebSockets = 'channel_websockets'   #
    # Outgoing_AMQP = 'outgoing_amqp'             #
    # Outgoing_WebSockets = 'outgoing_websockets' #
    # PubSub_Topic = 'pubsub_topic'               #

# ################################################################################################################################
# ################################################################################################################################

_object_alias = {}

_object_alias[_object_type.Cache] = 'cache_builtin'
_object_alias[_object_type.Channel_REST] = 'channel_plain_http'
_object_alias[_object_type.Confluence] = 'zato_generic_connection:cloud-confluence'
_object_alias[_object_type.Jira] = 'zato_generic_connection:cloud-jira'
_object_alias[_object_type.LDAP] = 'outgoing_ldap'
_object_alias[_object_type.Microsoft_365] = ['zato_generic_connection:cloud-confluence', 'cloud-microsoft-365']
_object_alias[_object_type.Odoo] = 'outconn_odoo'
_object_alias[_object_type.Outgoing_SOAP] = 'outconn_soap'
_object_alias[_object_type.Security] = ['def_sec', 'security_name']
_object_alias[_object_type.SQL] = 'outconn_sql'

# ################################################################################################################################
# ################################################################################################################################

_attr_alias = {}

_attr_alias[_object_type.SQL] = {
    'type':'engine'
}

# ################################################################################################################################
# ################################################################################################################################

_attr_default = {}

_attr_default[_object_type.Cache] = {
    'is_active': True,
    'is_default': False,
    'max_size': 10000,
    'max_item_size': 1000000,
    'sync_method': 'in-background',
    'persistent_storage': 'sqlite',
    'cache_type': 'builtin'
}

_attr_default[_object_type.Confluence] = {
    'is_active': True,
    'is_cloud': True,
    'api_version': 'v1'
}

_attr_default[_object_type.Email_IMAP] = {
    'is_active': True,
    'timeout': 30,
    'debug_level': 0,
    'mode': 'ssl',
    'get_criteria': 'ALL'
}

_attr_default[_object_type.Email_SMTP] = {
    'is_active': True,
    'timeout': 30,
    'is_debug': False,
    'mode': 'starttls',
    'ping_address': 'example@example.com'
}

_attr_default[_object_type.Jira] = {
    'is_active': True,
    'is_cloud': True,
    'api_version': 'v2'
}

_attr_default[_object_type.Odoo] = {
    'is_active': True,
    'protocol': 'jsonrpc',
    'pool_size': 10
}

_attr_default[_object_type.Cache] = {
    'is_active': True,
    'is_default': False,
    'max_size': 10000,
    'max_item_size': 1000000,
    'extend_expiry_on_get': True,
    'extend_expiry_on_set': False,
    'sync_method': 'in-background',
    'persistent_storage': 'sqlite'
}

_attr_default[_object_type.Scheduler] = {
    'is_active': True,
    'job_type': 'interval_based',
    'weeks': 0,
    'days': 0,
    'hours': 0,
    'minutes': 1,
    'seconds': 0,
    'repeats': 0
}

# ################################################################################################################################
# ################################################################################################################################

class ModuleCtx:

    # This is always the same
    Cluster_ID = 1
    Initial_Wait_Time = 10
    Missing_Wait_Time = 1
    ignore_missing_includes = False

    ObjectType  = _object_type
    ObjectAlias = _object_alias

# ################################################################################################################################
# ################################################################################################################################
