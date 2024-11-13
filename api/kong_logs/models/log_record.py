
from odoo import models, fields

class LogRecord(models.Model):
    _name = 'log.record'
    _description = 'Kong Log Record'

    error_message = fields.Text(string="Error Message")
    received_at = fields.Datetime(string="Received At", default=fields.Datetime.now)
    status_code = fields.Char(string="Status Code")
    endpoint = fields.Char(string="Endpoint")
    method = fields.Char(string="HTTP Method")
    log_content = fields.Text(string="Log Content")