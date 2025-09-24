# -*- coding: utf-8 -*-

"""
Copyright (C) 2024, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import mimetypes
import posixpath
from logging import getLogger
from pathlib import Path

# Django
from django.http import FileResponse, Http404, HttpResponseNotModified
from django.template.response import TemplateResponse
from django.utils._os import safe_join
from django.utils.http import http_date, parse_http_date

# Zato
from zato.common.crypto.api import CryptoManager
from zato.common.json_internal import loads
from zato.common.util.platform_ import is_windows

# ################################################################################################################################
# ################################################################################################################################

logger = getLogger(__name__)

# ################################################################################################################################
# ################################################################################################################################

windows_disabled = [
    'abc123',
    'zxc456'
]

# ################################################################################################################################
# ################################################################################################################################

def get_template_response(req, template_name, return_data):

    if is_windows:
        for name in windows_disabled:
            if name in template_name:
                return_data['is_disabled'] = True
                return_data['disabled_template_name'] = template_name

    return TemplateResponse(req, template_name, return_data)

# ################################################################################################################################
# ################################################################################################################################

def get_user_profile(user, needs_logging=True):
    if needs_logging:
        logger.info('Getting profile for user `%s`', user)

    from zato.admin.web.models import UserProfile

    try:
        user_profile = UserProfile.objects.get(user=user)
        if needs_logging:
            logger.info('Found an existing profile for user `%s`', user)
    except UserProfile.DoesNotExist:

        if needs_logging:
            logger.info('Did not find an existing profile for user `%s`', user)

        user_profile = UserProfile(user=user)
        user_profile.save()

        if needs_logging:
            logger.info('Created a profile for user `%s`', user)

    finally:
        if needs_logging:
            logger.info('Returning a user profile for `%s`', user)
        return user_profile

# ################################################################################################################################
# ################################################################################################################################

def set_user_profile_totp_key(user_profile, zato_secret_key, totp_key, totp_key_label=None, opaque_attrs=None):

    if not opaque_attrs:
        opaque_attrs = user_profile.opaque1
        opaque_attrs = loads(opaque_attrs) if opaque_attrs else {}

    cm = CryptoManager(secret_key=zato_secret_key)

    # TOTP key is always encrypted
    totp_key = cm.encrypt(totp_key.encode('utf8'))
    opaque_attrs['totp_key'] = totp_key

    # .. and so is its label
    if totp_key_label:
        totp_key_label = cm.encrypt(totp_key_label.encode('utf8'))
        opaque_attrs['totp_key_label'] = totp_key_label

    return opaque_attrs

# ################################################################################################################################
# ################################################################################################################################

#
# Taken from Django to change the content type from application/json to application/javascript.
#
def static_serve(request, path, document_root=None, show_indexes=False):
    """
    Serve static files below a given point in the directory structure.

    To use, put a URL pattern such as::

        from django.views.static import serve

        path('<path:path>', serve, {'document_root': '/path/to/my/files/'})

    in your URLconf. You must provide the ``document_root`` param. You may
    also set ``show_indexes`` to ``True`` if you'd like to serve a basic index
    of the directory.  This index view will use the template hardcoded below,
    but if you'd like to override it, you can create a template called
    ``static/directory_index.html``.
    """

    path = posixpath.normpath(path).lstrip("/")
    fullpath = Path(safe_join(document_root, path))
    if fullpath.is_dir():
        if show_indexes:
            return directory_index(path, fullpath)
        raise Http404('Directory indexes are not allowed here.')
    if not fullpath.exists():
        raise Http404(f'Path {fullpath} does not exist')
    # Respect the If-Modified-Since header.
    statobj = fullpath.stat()
    if not was_modified_since(
        request.META.get("HTTP_IF_MODIFIED_SINCE"), statobj.st_mtime
    ):
        return HttpResponseNotModified()
    content_type, encoding = mimetypes.guess_type(str(fullpath))
    content_type = content_type or "application/octet-stream"

    # Explicitly set the content type for JSON resources.
    # Note that this needs to be combined with SECURE_CONTENT_TYPE_NOSNIFF=False in settings.py
    if fullpath.name.endswith('.js'):
        content_type = 'application/javascript'

    response = FileResponse(fullpath.open("rb"), content_type=content_type)
    response.headers["Last-Modified"] = http_date(statobj.st_mtime)
    if encoding:
        response.headers["Content-Encoding"] = encoding
    return response

def was_modified_since(header=None, mtime=0):
    """
    Was something modified since the user last downloaded it?

    header
      This is the value of the If-Modified-Since header.  If this is None,
      I'll just return True.

    mtime
      This is the modification time of the item we're talking about.
    """
    try:
        if header is None:
            raise ValueError
        header_mtime = parse_http_date(header)
        if int(mtime) > header_mtime:
            raise ValueError
    except (ValueError, OverflowError):
        return True
    return False

# ################################################################################################################################
# ################################################################################################################################

def get_pubsub_security_definitions(request, form_type='edit', context='subscription'):

    response = request.zato.client.invoke('zato.security.basic-auth.get-list', {
        'cluster_id': request.zato.cluster_id,
    })

    # Define names to filter out
    filtered_names = {
        'Rule engine default user',
        'admin.invoke',
        'ide_publisher'
    }

    choices = []
    if response.ok:
        # Get already used security definitions based on context
        used_sec_ids = set()

        if form_type == 'create':
            if context == 'subscription':
                # For subscriptions page, exclude definitions used by other subscriptions
                subscriptions_response = request.zato.client.invoke('zato.pubsub.subscription.get-list', {
                    'cluster_id': request.zato.cluster_id,
                })
                if subscriptions_response.ok:
                    # Create a mapping of security names to IDs from the basic auth definitions
                    sec_name_to_id = {}
                    for sec_def in response.data:
                        sec_name_to_id[sec_def['name']] = sec_def['id']

                    for item in subscriptions_response.data:
                        # Check both security_id and sec_name fields
                        sec_id = None
                        if item.get('security_id'):
                            sec_id = item['security_id']
                        elif item.get('sec_name'):
                            # Map security name to ID
                            sec_name = item['sec_name']
                            sec_id = sec_name_to_id.get(sec_name)

                        if sec_id:
                            used_sec_ids.add(sec_id)
            elif context == 'permission':
                # For permissions page, exclude definitions used by other permissions
                permissions_response = request.zato.client.invoke('zato.pubsub.permission.get-list', {
                    'cluster_id': request.zato.cluster_id,
                })
                if permissions_response.ok:
                    for item in permissions_response.data:
                        if item.get('sec_base_id'):
                            used_sec_ids.add(item['sec_base_id'])
            elif context == 'client':
                # For client context, we might want different filtering logic
                # For now, treat it similar to permissions since clients are related to permissions
                permissions_response = request.zato.client.invoke('zato.pubsub.permission.get-list', {
                    'cluster_id': request.zato.cluster_id,
                })
                if permissions_response.ok:
                    for item in permissions_response.data:
                        if item.get('sec_base_id'):
                            used_sec_ids.add(item['sec_base_id'])

        for item in response.data:
            is_not_used = item['id'] not in used_sec_ids
            is_not_filtered = item['name'] not in filtered_names
            is_not_zato = not item['name'].startswith('zato')

            if is_not_used and is_not_filtered and is_not_zato:
                choices.append({
                    'id': item['id'],
                    'name': item['name']
                })

    return choices

def get_pubsub_security_choices(request, form_type='edit', context='subscription'):
    """ Get filtered security definitions for Django form choices (tuples format).
    """
    definitions = get_pubsub_security_definitions(request, form_type, context)
    return [(item['id'], item['name']) for item in definitions]

# ################################################################################################################################
# ################################################################################################################################

def get_service_list(request):

    response = request.zato.client.invoke('zato.service.get-list', {
        'cluster_id': request.zato.cluster_id,
    })

    services = []
    if response.ok:
        for item in response.data:
            services.append({
                'service_name': item['name']
            })

    return services

# ################################################################################################################################
# ################################################################################################################################
