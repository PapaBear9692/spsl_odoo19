import datetime
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError


PASSWORD_MIN_LENGTH = 10
PASSWORD_EXPIRY_DAYS = 90


class ResUsers(models.Model):
    _inherit = 'res.users'

    password_set_date = fields.Datetime(
        string='Password Set Date',
        copy=False,
        tracking=True,
        help='Timestamp of the last password change. Used to enforce password expiry.',
    )

    def _set_password(self):
        """Override to validate password complexity before storing."""
        for user in self:
            if user.password:
                self._validate_password_complexity(user.password)
        super()._set_password()
        # Record when the password was set
        self.write({'password_set_date': fields.Datetime.now()})

    @api.model
    def _validate_password_complexity(self, password):
        """Validate password meets complexity requirements.

        Rules:
        - Minimum 10 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        errors = []

        if len(password) < PASSWORD_MIN_LENGTH:
            errors.append(
                _("Password must be at least %d characters long.") % PASSWORD_MIN_LENGTH
            )

        if not re.search(r'[A-Z]', password):
            errors.append(_("Password must contain at least one uppercase letter."))

        if not re.search(r'[a-z]', password):
            errors.append(_("Password must contain at least one lowercase letter."))

        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one digit."))

        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\`~]', password):
            errors.append(_("Password must contain at least one special character."))

        if errors:
            raise UserError(_(
                "Password does not meet security requirements:\n%s"
            ) % '\n'.join('- %s' % e for e in errors))

    def _check_credentials(self, credential, env):
        """Override to check password expiry after successful credential validation."""
        auth_info = super()._check_credentials(credential, env)

        # Only check expiry for password-based interactive logins
        if credential.get('type') == 'password' and auth_info.get('auth_method') == 'password':
            self._check_password_expiry()

        return auth_info

    def _check_password_expiry(self):
        """Raise AccessDenied if the password has expired (older than 90 days).

        Skipped for system users (uid=1) to avoid lockout.
        """
        for user in self:
            if user.id == self.env.ref('base.user_root').id:
                continue

            if not user.password_set_date:
                # User never had a recorded password date — set it now
                user.sudo().password_set_date = fields.Datetime.now()
                continue

            expiry_date = user.password_set_date + datetime.timedelta(days=PASSWORD_EXPIRY_DAYS)
            if fields.Datetime.now() > expiry_date:
                raise UserError(_(
                    "Your password has expired. "
                    "Please contact an administrator to reset your password, "
                    "or change it from your preferences."
                ))

