# -*- coding: utf-8 -*-

"""
Copyright (C) 2025, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from logging import getLogger

# Zato
from zato.common.typing_ import cast_
from zato.server.connection.cloud.microsoft_365 import Microsoft365Client
from zato.server.connection.queue import Wrapper

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from zato.common.typing_ import any_
    from O365 import Account as Office365Account
    Office365Account = Office365Account

# ################################################################################################################################
# ################################################################################################################################

logger = getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

class CloudMicrosoft365Wrapper(Wrapper):
    """ Wraps a queue of connections to Microsoft 365.
    """
    def __init__(self, config:'any_', server:'any_') -> 'None':
        config['auth_url'] = config['address']
        super(CloudMicrosoft365Wrapper, self).__init__(config, 'Microsoft 365', server)

# ################################################################################################################################

    def add_client(self):

        try:
            conn = Microsoft365Client(self.config)
            _ = self.client.put_client(conn)
        except Exception as e:
            logger.warning('Caught an exception while adding a Microsoft 365 client (%s); e:`%s`',
                self.config['name'], e)

# ################################################################################################################################

    def ping(self):
        with self.client() as client:
            client = cast_('Microsoft365Client', client)
            client.ping()

# ################################################################################################################################
# ################################################################################################################################
