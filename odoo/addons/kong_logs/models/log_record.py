
from odoo import models, fields

class LogRecord(models.Model):
    _name = 'log.record'
    _description = 'Kong Log Record'

    log_content = fields.Text("Log Content")
    status_code = fields.Char("Status Code")
    endpoint = fields.Char("Endpoint")
    method = fields.Char("HTTP Method")
    timestamp = fields.Datetime("Received At", default=fields.Datetime.now)
