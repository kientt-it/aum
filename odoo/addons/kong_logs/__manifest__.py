
{
    'name': 'Kong Logs',
    'version': '1.0',
    'summary': 'Module lưu trữ log từ Kong trong Odoo',
    'author': 'Your Name',
    'category': 'Tools',
    'depends': ['base', 'fastapi'],
    'data': [
        'views/log_record_views.xml',
    ],
    'installable': True,
    'application': False,
}
