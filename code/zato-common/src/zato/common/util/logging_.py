# -*- coding: utf-8 -*-

"""
Copyright (C) 2024, Zato Source s.r.o. https://zato.io

Licensed under AGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
import os
from logging import Formatter

# Zato
from zato.common.util.platform_ import is_posix

# ################################################################################################################################
# ################################################################################################################################

logging_conf_contents = """
loggers:
    '':
        level: INFO
        handlers: [stdout, default]
    'gunicorn.main':
        level: INFO
        handlers: [stdout, default]
    'pytds':
        level: WARN
        handlers: [stdout, default]
    zato:
        level: INFO
        handlers: [stdout, default]
        qualname: zato
        propagate: false
    zato_rest:
        level: INFO
        handlers: [stdout, default]
        qualname: zato
        propagate: false
    zato_access_log:
        level: INFO
        handlers: [http_access_log]
        qualname: zato_access_log
        propagate: false
    zato_admin:
        level: INFO
        handlers: [admin]
        qualname: zato_admin
        propagate: false
    zato_audit_pii:
        level: INFO
        handlers: [stdout, audit_pii]
        qualname: zato_audit_pii
        propagate: false
    zato_connector:
        level: INFO
        handlers: [connector]
        qualname: zato_connector
        propagate: false
    zato_scheduler:
        level: INFO
        handlers: [stdout, scheduler]
        qualname: zato_scheduler
        propagate: false
handlers:
    default:
        formatter: default
        class: {log_handler_class}
        filename: './logs/server.log'
        mode: 'a'
        maxBytes: {server_log_max_size}
        backupCount: {server_log_backup_count}
        encoding: 'utf8'
    stdout:
        formatter: colour
        class: logging.StreamHandler
        stream: ext://sys.stdout
    http_access_log:
        formatter: default
        class: {log_handler_class}
        filename: './logs/http_access.log'
        mode: 'a'
        maxBytes: {server_log_max_size}
        backupCount: {server_log_backup_count}
        encoding: 'utf8'
    admin:
        formatter: default
        class: {log_handler_class}
        filename: './logs/admin.log'
        mode: 'a'
        maxBytes: 20000000
        backupCount: 10
        encoding: 'utf8'
    audit_pii:
        formatter: default
        class: logging.handlers.RotatingFileHandler
        filename: './logs/audit-pii.log'
        mode: 'a'
        maxBytes: 20000000
        backupCount: 10
        encoding: 'utf8'
    connector:
        formatter: default
        class: {log_handler_class}
        filename: './logs/connector.log'
        mode: 'a'
        maxBytes: 20000000
        backupCount: 10
        encoding: 'utf8'
    scheduler:
        formatter: default
        class: {log_handler_class}
        filename: './logs/scheduler.log'
        mode: 'a'
        maxBytes: 20000000
        backupCount: 10
        encoding: 'utf8'

formatters:
    audit_pii:
        format: '%(message)s'
    default:
        format: '%(asctime)s - %(levelname)s - %(process)d:%(threadName)s - %(name)s:%(lineno)d - %(message)s'
    http_access_log:
        format: '%(remote_ip)s %(cid_resp_time)s "%(channel_name)s" [%(req_timestamp)s] "%(method)s %(path)s %(http_version)s" %(status_code)s %(response_size)s "-" "%(user_agent)s"'
    colour:
        format: '%(asctime)s - %(levelname)s - %(process)d:%(threadName)s - %(name)s:%(lineno)d - %(message)s'
        (): zato.common.util.api.ColorFormatter

version: 1
""" # noqa: E501

# ################################################################################################################################
# ################################################################################################################################

# Based on http://stackoverflow.com/questions/384076/how-can-i-make-the-python-logging-output-to-be-colored
class ColorFormatter(Formatter):

    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
    RESET_SEQ = '\033[0m'
    COLOR_SEQ = '\033[1;%dm'
    BOLD_SEQ = '\033[1m'

    COLORS = {
      'WARNING': YELLOW,
      'INFO': WHITE,
      'DEBUG': BLUE,
      'CRITICAL': YELLOW,
      'ERROR': RED,
      'TRACE1': YELLOW
    }

    def __init__(self, fmt):
        self.use_color = True if is_posix else False
        super(ColorFormatter, self).__init__(fmt)

# ################################################################################################################################

    def formatter_msg(self, msg, use_color=True):
        if use_color:
            msg = msg.replace('$RESET', self.RESET_SEQ).replace('$BOLD', self.BOLD_SEQ)
        else:
            msg = msg.replace('$RESET', '').replace('$BOLD', '')
        return msg

# ################################################################################################################################

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in self.COLORS:
            fore_color = 30 + self.COLORS[levelname]
            levelname_color = self.COLOR_SEQ % fore_color + levelname + self.RESET_SEQ
            record.levelname = levelname_color

        return Formatter.format(self, record)

# ################################################################################################################################
# ################################################################################################################################

def get_logging_conf_contents() -> 'str':
    # type: (str) -> str

    # We import it here to make CLI work faster
    from zato.common.util.platform_ import is_linux

    linux_log_handler_class     = 'logging.handlers.RotatingFileHandler' # Previously = ConcurrentRotatingFileHandler
    non_linux_log_handler_class = 'logging.handlers.RotatingFileHandler'

    # Under Windows, we cannot have multiple processes access the same log file
    log_handler_class = linux_log_handler_class if is_linux else non_linux_log_handler_class

    # This can be overridden by users
    if server_log_max_size := os.environ.get('Zato_Server_Log_Max_Size'):
        server_log_max_size = int(server_log_max_size)
    else:
        server_log_max_size = 1000000000 # 1 GB by default

    # This can be overridden by users
    if server_log_backup_count := os.environ.get('Zato_Server_Log_Backup_Count'):
        server_log_backup_count = int(server_log_backup_count)
    else:
        server_log_backup_count = 2

    return logging_conf_contents.format(
        log_handler_class=log_handler_class,
        server_log_max_size=server_log_max_size,
        server_log_backup_count=server_log_backup_count,
    )

# ################################################################################################################################
# ################################################################################################################################
