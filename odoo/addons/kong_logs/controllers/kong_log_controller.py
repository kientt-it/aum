
from odoo import http
import json
from odoo.http import request

class KongLogController(http.Controller):
    @http.route('/api/logs', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_log(self, **kwargs):
        # Nhận dữ liệu log từ request
        log_data = request.jsonrequest

        # Tạo bản ghi log trong model log.record
        request.env['log.record'].sudo().create({
            'log_content': json.dumps(log_data),
            'status_code': log_data.get('status', ''),
            'endpoint': log_data.get('url', ''),
            'method': log_data.get('method', ''),
        })

        return {"status": "Log received"}
