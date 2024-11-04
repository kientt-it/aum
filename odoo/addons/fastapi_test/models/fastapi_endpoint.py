from odoo import models, fields


class FastAPIEndpoint(models.Model):
    _inherit = 'fastapi.endpoint'

    app = fields.Selection(
        selection_add=[('my_app', 'My FastAPI App')],
        ondelete={'my_app': 'cascade'}
    )

    def _get_fastapi_routers(self):
        routers = super()._get_fastapi_routers()
        if self.app == 'my_app':
            from ..routers import user, order
            routers.extend([user.router, order.router])
        return routers



