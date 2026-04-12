# Copyright 2026 SPSL - Smart Printing Service Limited
# License LGPL-3 (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class NotificationDispatcher(models.Model):
    _name = 'spsl.notification.dispatcher'
    _description = 'SPSL Notification Dispatcher'

    MAX_RETRIES = 3
    RETRY_INTERVAL_MINUTES = 15

    def dispatch(self, event_code, document, context=None):
        _logger = self.env['ir.logging'].sudo()
        _logger.create({'name': 'spsl_core', 'level': 'info', 'message': f'DISPATCH START: event_code={event_code}', 'type': 'server'})
        
        self = self.env['spsl.notification.dispatcher']
        context = context or {}
        
        template = self.env['spsl.notification.template'].search([
            ('event_code', '=', event_code),
            ('active', '=', True),
        ], limit=1)
        
        _logger.create({'name': 'spsl_core', 'level': 'info', 'message': f'TEMPLATE: {template.name if template else "NOT FOUND"}', 'type': 'server'})
        
        if not template:
            raise UserError(f'No active notification template found for event code: {event_code}')
        
        recipients = template.get_recipients(document)
        
        _logger.create({'name': 'spsl_core', 'level': 'info', 'message': f'RECIPIENTS count: {len(recipients) if recipients else 0}', 'type': 'server'})
        
        if not recipients:
            return False
        
        recipients = self._filter_by_preferences(recipients, template, document)
        
        if not recipients:
            return True
        
        subject = template.render_template(document, 'subject')
        body = template.render_template(document, 'body')
        
        channels = template.channels.mapped('code') if template.channels else []
        
        if not channels:
            channels = ['in_app']
        
        _logger.create({'name': 'spsl_core', 'level': 'info', 'message': f'CHANNELS: {channels}', 'type': 'server'})
        
        results = []
        for recipient in recipients:
            for channel in channels:
                _logger.create({'name': 'spsl_core', 'level': 'info', 'message': f'DISPATCH to={recipient.login} channel={channel}', 'type': 'server'})
                result = self._dispatch_to_channel(
                    template, recipient, channel, subject, body, document, context
                )
                results.append(result)
        
        _logger.create({'name': 'spsl_core', 'level': 'info', 'message': f'DISPATCH DONE: results={results}', 'type': 'server'})
        
        return any(results)

    def _filter_by_preferences(self, recipients, template, document):
        filtered = self.env['res.users']
        for user in recipients:
            if template.is_mandatory:
                filtered |= user
                continue
            
            preference = getattr(user, 'notification_preference', 'email')
            channels = template.channels.mapped('code') if template.channels else []
            
            if not channels:
                if preference != 'none':
                    filtered |= user
            else:
                for channel in channels:
                    if channel == 'email' and preference in ['email', 'both']:
                        filtered |= user
                        break
                    elif channel == 'sms' and preference in ['sms', 'both']:
                        filtered |= user
                        break
                    elif channel == 'in_app':
                        filtered |= user
                        break
        
        return filtered

    def _dispatch_to_channel(self, template, recipient, channel, subject, body, document, context):
        log_vals = {
            'event_code': template.event_code,
            'template_id': template.id,
            'channel': channel,
            'recipient_id': recipient.id,
            'recipient_email': recipient.email,
            'recipient_phone': getattr(recipient, 'phone', False),
            'status': 'queued',
        }
        
        if document:
            log_vals['document_ref'] = f'{document._name},{document.id}'
        
        handler_method = f'_send_{channel}'
        if hasattr(self, handler_method):
            if channel == 'sms':
                recipient_phone = getattr(recipient, 'phone', False)
                success, error_msg = self._send_sms(recipient, recipient_phone, body)
            elif channel == 'push':
                success, error_msg = self._send_push(recipient, subject, body)
            else:
                success, error_msg = getattr(self, handler_method)(
                    template, recipient, subject, body, document, context
                )
            
            if success:
                log_vals['status'] = 'sent'
                log_vals['sent_date'] = fields.Datetime.now()
            else:
                log_vals['status'] = 'failed'
                log_vals['error_message'] = error_msg
                log_vals['retry_count'] = 1
                log_vals['next_retry_date'] = fields.Datetime.now() + timedelta(minutes=self.RETRY_INTERVAL_MINUTES)
        
        log = self.env['spsl.notification.log'].create(log_vals)
        
        if log_vals['status'] == 'failed':
            self._schedule_retry(log, template, recipient, channel, subject, body, document, context)
        
        return log_vals['status'] != 'failed'

    def _send_in_app(self, template, recipient, subject, body, document, context):
        try:
            self.env['mail.message'].create({
                'model': recipient._name,
                'res_id': recipient.id,
                'body': body,
                'subject': subject,
                'message_type': 'notification',
                'subtype_id': self.env.ref('mail.mt_note').id,
            })
            return True, None
        except Exception as e:
            return False, str(e)

    def _send_email(self, template, recipient, subject, body, document, context):
        try:
            if not recipient.email:
                return False, 'Recipient has no email address'
            
            mail_values = {
                'email_from': self.env.company.email if hasattr(self.env, 'company') else 'noreply@spsl.com.bd',
                'email_to': recipient.email,
                'subject': subject,
                'body_html': body,
            }
            
            if document:
                mail_values['model'] = document._name
                mail_values['res_id'] = document.id
            
            mail = self.env['mail.mail'].create(mail_values)
            mail.send()
            
            return True, None
        except Exception as e:
            return False, str(e)

    def _send_sms(self, recipient, phone_number, body):
        import re
        bangladesh_phone_pattern = r'^\+8801[3-9]\d{9}$'
        if not phone_number or not re.match(bangladesh_phone_pattern, phone_number):
            return False, 'Invalid Bangladesh mobile number format. Expected: +8801XXXXXXXXX'
        
        is_bangla = any('\u0980' <= char <= '\u09FF' for char in body)
        max_length = 70 if is_bangla else 160
        truncated_body = body[:max_length]
        
        log_vals = {
            'event_code': 'SMS_STUB',
            'channel': 'sms',
            'recipient_id': recipient.id if recipient else False,
            'recipient_phone': phone_number,
            'status': 'queued',
            'error_message': 'SMS integration pending — Mutho API to be connected in Phase 13',
        }
        
        self.env['spsl.notification.log'].create(log_vals)
        
        return True, None

    def _send_push(self, recipient, subject, body, url=None):
        push_sub = getattr(recipient, 'push_subscription', False)
        
        if not push_sub:
            log_vals = {
                'event_code': 'PUSH_STUB',
                'channel': 'push',
                'recipient_id': recipient.id,
                'status': 'skipped',
                'error_message': 'No push subscription registered',
            }
            self.env['spsl.notification.log'].create(log_vals)
            return True, None
        
        log_vals = {
            'event_code': 'PUSH_STUB',
            'channel': 'push',
            'recipient_id': recipient.id,
            'status': 'queued',
            'error_message': 'Web Push integration pending — VAPID to be configured in Phase 13',
        }
        
        self.env['spsl.notification.log'].create(log_vals)
        
        return True, None

    def _schedule_retry(self, log, template, recipient, channel, subject, body, document, context):
        pass

    def process_retry(self):
        logs = self.env['spsl.notification.log'].search([
            ('status', '=', 'failed'),
            ('retry_count', '<', self.MAX_RETRIES),
            ('next_retry_date', '<=', fields.Datetime.now()),
        ])

        for log in logs:
            template = log.template_id
            recipient = log.recipient_id
            channel = log.channel

            document = None
            if log.document_ref:
                try:
                    model_name, res_id = log.document_ref.split(',')
                    document = self.env[model_name].browse(int(res_id))
                except Exception:
                    pass

            subject = template.render_template(document, 'subject') if document else ''
            body = template.render_template(document, 'body') if document else ''

            if channel == 'sms':
                phone = getattr(recipient, 'phone', False)
                success, error_msg = self._send_sms(recipient, phone, body)
            elif channel == 'push':
                success, error_msg = self._send_push(recipient, subject, body)
            else:
                success, error_msg = self._dispatch_to_channel(
                    template, recipient, channel, subject, body, document, {}
                )

            log.write({
                'status': 'sent' if success else 'failed',
                'sent_date': fields.Datetime.now() if success else False,
                'error_message': error_msg if not success else False,
                'retry_count': log.retry_count + 1,
                'next_retry_date': fields.Datetime.now() + timedelta(
                    minutes=(log.retry_count + 1) * self.RETRY_INTERVAL_MINUTES
                ) if not success and log.retry_count + 1 < self.MAX_RETRIES else False,
            })

        return len(logs)