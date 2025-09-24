# -*- coding: utf-8 -*-

"""
Copyright (C) Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import logging
from traceback import format_exc

# Django
from django.http import HttpResponse, HttpResponseServerError
from django.template.response import TemplateResponse

# Zato
from zato.admin.settings import delivery_friendly_name
from zato.admin.web.forms.outgoing.amqp_ import CreateForm, EditForm
from zato.admin.web.views import Delete as _Delete, Index as _Index, invoke_action_handler, method_allowed
from zato.common.json_internal import dumps
from zato.common.odb.model import OutgoingAMQP

# ################################################################################################################################
# ################################################################################################################################

logger = logging.getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

def _get_edit_create_message(params, prefix=''):
    """ Creates a base dictionary which can be used by both 'edit' and 'create' actions.
    """
    return {
        'id': params.get('id'),
        'cluster_id': params['cluster_id'],
        'name': params[prefix + 'name'],
        'is_active': bool(params.get(prefix + 'is_active')),
        'address': params.get(prefix + 'address'),
        'username': params.get(prefix + 'username'),
        'password': params.get(prefix + 'password'),
        'delivery_mode': params[prefix + 'delivery_mode'],
        'priority': params[prefix + 'priority'],
        'content_type': params.get(prefix + 'content_type'),
        'content_encoding': params.get(prefix + 'content_encoding'),
        'expiration': params.get(prefix + 'expiration'),
        'pool_size': params.get(prefix + 'pool_size'),
        'user_id': params.get(prefix + 'user_id'),
        'app_id': params.get(prefix + 'app_id'),
    }

# ################################################################################################################################
# ################################################################################################################################

def _edit_create_response(verb, id, name, delivery_mode_text):
    return_data = {'id': id,
                   'message': 'Successfully {} outgoing AMQP connection `{}`'.format(verb, name),
                   'delivery_mode_text': delivery_mode_text,
                }
    return HttpResponse(dumps(return_data), content_type='application/javascript')

# ################################################################################################################################
# ################################################################################################################################

class Index(_Index):
    method_allowed = 'GET'
    url_name = 'out-amqp'
    template = 'zato/outgoing/amqp.html'
    service_name = 'zato.outgoing.amqp.get-list'
    output_class = OutgoingAMQP
    paginate = True

    class SimpleIO(_Index.SimpleIO):
        input_required = ('cluster_id',)
        output_required = ('id', 'name', 'address', 'username', 'password', 'is_active', 'delivery_mode', 'priority',
            'content_type', 'content_encoding', 'expiration', 'pool_size', 'user_id', 'app_id', 'delivery_mode_text')
        output_repeated = True

    def handle(self):
        create_form = CreateForm()
        edit_form = EditForm(prefix='edit')

        for item in self.items:
            item.delivery_mode_text = delivery_friendly_name[item.delivery_mode]

        return {
            'create_form': create_form,
            'edit_form': edit_form,
        }

# ################################################################################################################################
# ################################################################################################################################

@method_allowed('POST')
def create(req):
    try:
        request = _get_edit_create_message(req.POST)
        response = req.zato.client.invoke('zato.outgoing.amqp.create', request)
        delivery_mode_text = delivery_friendly_name[req.POST['delivery_mode']]

        return _edit_create_response('created', response.data.id, req.POST['name'], delivery_mode_text)
    except Exception:
        msg = 'Outgoing AMQP connection could not be created, e:`{}`'.format(format_exc())
        logger.error(msg)
        return HttpResponseServerError(msg)

# ################################################################################################################################
# ################################################################################################################################

@method_allowed('POST')
def edit(req):
    try:
        request = _get_edit_create_message(req.POST, 'edit-')
        req.zato.client.invoke('zato.outgoing.amqp.edit', request)
        delivery_mode_text = delivery_friendly_name[req.POST['edit-delivery_mode']]

        return _edit_create_response('updated', req.POST['id'], req.POST['edit-name'], delivery_mode_text)
    except Exception:
        msg = 'Outgoing AMQP connection could not be updated, e:`{}`'.format(format_exc())
        logger.error(msg)
        return HttpResponseServerError(msg)

# ################################################################################################################################
# ################################################################################################################################

class Delete(_Delete):
    url_name = 'out-amqp-delete'
    error_message = 'Could not delete outgoing AMQP connection'
    service_name = 'zato.outgoing.amqp.delete'

# ################################################################################################################################
# ################################################################################################################################

@method_allowed('GET')
def invoke(req, conn_id, conn_name, conn_slug):

    return_data = {
        'conn_id': conn_id,
        'conn_name': conn_name,
        'cluster_id': req.zato.cluster_id,
    }

    return TemplateResponse(req, 'zato/outgoing/amqp-invoke.html', return_data)

# ################################################################################################################################
# ################################################################################################################################

@method_allowed('POST')
def invoke_action(req, conn_name):
    return invoke_action_handler(req, 'zato.outgoing.amqp.publish', ('conn_name', 'request_data', 'exchange', 'routing_key'))

# ################################################################################################################################
# ################################################################################################################################
