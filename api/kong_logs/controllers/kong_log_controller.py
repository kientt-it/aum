
from odoo import http, fields
import json
from odoo.http import request

class KongLogController(http.Controller):
    @http.route('/api/logs', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_log(self, **kwargs):
        print("KongLogController is being accessed.")

        # Nhận dữ liệu log từ request
        log_data = json.loads(request.httprequest.data)
        error_message = log_data.get('response', {}).get('error', '')

        # Tạo bản ghi log trong model log.record
        request.env['log.record'].sudo().create({
            'received_at': fields.Datetime.now(),
            'status_code': str(log_data.get('response', {}).get('status_code', '')),
            'endpoint': log_data.get('request', {}).get('endpoint', ''),
            'method': log_data.get('request', {}).get('method', ''),
            'log_content': json.dumps(log_data),
            'error_message': error_message,
        })

        return {"status": "Log received"}


