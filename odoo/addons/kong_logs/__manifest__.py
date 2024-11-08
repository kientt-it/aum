
{
    'name': 'API Logs',
    'version': '1.0',
    'summary': 'Module lưu trữ log từ Kong trong Odoo',
    'author': 'Trung Kien',
    'category': 'Tool Log',
    'website': 'http://www.konglogs.com',
    'depends': ['base', 'fastapi'],
    'data': [
        'security/ir.model.access.csv',
        'views/log_record_views.xml',
        'views/log_record_menus.xml',
    ],
    'installable': True,
    'application': False,
}
