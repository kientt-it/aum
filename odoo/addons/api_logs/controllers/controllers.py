# -*- coding: utf-8 -*-
# from odoo import http


# class ApiLogs(http.Controller):
#     @http.route('/api_logs/api_logs', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/api_logs/api_logs/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('api_logs.listing', {
#             'root': '/api_logs/api_logs',
#             'objects': http.request.env['api_logs.api_logs'].search([]),
#         })

#     @http.route('/api_logs/api_logs/objects/<model("api_logs.api_logs"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('api_logs.object', {
#             'object': obj
#         })
