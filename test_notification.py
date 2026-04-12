#!/usr/bin/env python3
import os
os.chdir('/home/unisoft/Work/smart_printing_service_limited')

import sys
sys.path.insert(0, '/home/unisoft/Work/smart_printing_service_limited')
sys.path.insert(0, '/home/unisoft/Work/smart_printing_service_limited/.venv/lib/python3.12/site-packages')

import odoo
from odoo.tools import config
config._init_config()
config['db_name'] = 'SPSL'

from odoo.modules.registry import Registry
from odoo import api

registry = Registry('SPSL')
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})
    
    user = env.user
    result = env['spsl.notification.dispatcher'].dispatch('NE-TEST-001', user)
    print(f"Dispatch result: {result}")
    
    logs = env['spsl.notification.log'].search([], order='id desc', limit=10)
    print(f"\nNotification Logs ({len(logs)} total):")
    for log in logs:
        print(f"  - {log.event_code} | {log.channel} | {log.status} | {log.recipient_id.name if log.recipient_id else 'N/A'}")