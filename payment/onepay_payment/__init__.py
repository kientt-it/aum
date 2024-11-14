# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.api import Environment
from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider

def post_init_hook(cr, registry):
    # Tạo môi trường env từ cr và registry
    from odoo import SUPERUSER_ID
    env = Environment(cr, SUPERUSER_ID, {})

    # Cấu hình provider "onepay"
    provider = env['payment.provider'].search([("code", "=", "onepay")], limit=1)
    if provider:
        provider._setup_provider("onepay")

    # Cấu hình bổ sung nếu cần thiết
    provider.write({
        'state': 'enabled',  # Kích hoạt nếu chưa
    })

# Define a function to be called when the module is uninstalled
def uninstall_hook(env):
    # Reset the payment provider for "vnpay"
    reset_payment_provider(env, "vnpay")