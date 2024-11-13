{
    'name': 'OnePay Payment',
    'version': '1.0',
    'category': 'Payment',
    'sequence': 1,
    'summary': 'Integration with OnePay payment gateway',
    'description': 'Module to integrate OnePay payment gateway with Odoo',
    'author': 'Test',
    'depends': ['base','payment'],
    'data': [
        'views/payment_onepay_template.xml',
        'views/payment_onepay_view.xml',
        # 'data/ir_cron.xml',
        # 'data/payment_provider_data.xml',
        # 'data/payment_method_data.xml',
        ],   
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "LGPL-3",
}