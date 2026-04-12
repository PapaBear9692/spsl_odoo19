from . import models


def post_init_hook(env):
    """Set security config parameters on module install.

    Uses set_param() which safely updates existing keys or creates new ones,
    avoiding the unique constraint violation that XML data records would cause.
    """
    ICP = env['ir.config_parameter'].sudo()

    # Session timeout: 30 minutes (1800 seconds)
    ICP.set_param('sessions.max_inactivity_seconds', '1800')

    # Login lockout: trigger after 5 failed attempts
    ICP.set_param('base.login_cooldown_after', '5')

    # Login lockout: 15-minute (900 seconds) cooldown
    ICP.set_param('base.login_cooldown_duration', '900')

    # Set password_set_date for existing users who have a password but no date recorded
    env.cr.execute("""
        UPDATE res_users
        SET password_set_date = NOW()
        WHERE password_set_date IS NULL
          AND password IS NOT NULL
    """)
