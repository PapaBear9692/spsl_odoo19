from odoo import models, fields, api


class NotificationLog(models.Model):
    _name = 'spsl.notification.log'
    _description = 'SPSL Notification Log'
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._generate_name(),
    )
    event_id = fields.Many2one(
        'spsl.notification.event',
        string='Event',
        required=True,
        index=True,
    )
    template_id = fields.Many2one(
        'spsl.notification.template',
        string='Template',
        index=True,
    )
    model = fields.Char(
        string='Model',
        index=True,
    )
    res_id = fields.Integer(
        string='Resource ID',
        index=True,
    )
    res_name = fields.Char(
        string='Resource Name',
        compute='_compute_res_name',
        store=True,
    )
    recipient_id = fields.Many2one(
        'res.partner',
        string='Recipient',
        index=True,
    )
    channel = fields.Selection(
        selection=[
            ('email', 'Email'),
            ('sms', 'SMS'),
        ],
        string='Channel',
        required=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='pending',
        required=True,
        index=True,
    )
    subject = fields.Char(
        string='Subject',
    )
    body = fields.Text(
        string='Body',
    )
    error_message = fields.Text(
        string='Error Message',
    )
    sent_date = fields.Datetime(
        string='Sent Date',
        index=True,
    )
    create_date = fields.Datetime(
        string='Created Date',
        readonly=True,
        index=True,
    )

    @api.depends('model', 'res_id')
    def _compute_res_name(self):
        for record in self:
            if record.model and record.res_id:
                res = self.env[record.model].browse(record.res_id)
                record.res_name = res.display_name if res.exists() else False
            else:
                record.res_name = False

    def _generate_name(self):
        sequence = self.env['ir.sequence'].next_by_code('spsl.notification.log')
        return sequence or f'NOT/{fields.Date.today().year}/0000'

    @api.model
    def _dispatch_notification(self, record, event, template, context):
        partner = record.partner_id if hasattr(record, 'partner_id') else False
        if not partner:
            return False
        preference = getattr(record, 'notification_preference', 'email')
        results = []
        if preference in ['email', 'both']:
            results.append(self._send_email(record, event, template, partner, context))
        if preference in ['sms', 'both']:
            results.append(self._send_sms(record, event, template, partner, context))
        return any(results)

    def _send_email(self, record, event, template, partner, context):
        try:
            self.env['mail.mail'].create({
                'email_from': self.env.company.email or 'noreply@spsl.com.bd',
                'email_to': partner.email,
                'subject': template.subject or event.name,
                'body_html': template.body_html or '',
            })
            return True
        except Exception as e:
            return False

    def _send_sms(self, record, event, template, partner, context):
        return True