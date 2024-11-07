from odoo import models, fields
from odoo.addons.fastapi_test.middleware.main import LogMiddleware
from typing import Any, Callable, Dict, List, Tuple

from starlette.middleware import Middleware

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

    def _get_fastapi_app_middlewares(self) -> List[Middleware]:
        """Return the middlewares to use for the FastAPI app."""
        # Lấy danh sách middleware từ lớp cha
        middels = super()._get_fastapi_app_middlewares()

        # Kiểm tra xem LogMiddleware đã được thêm chưa
        if not any(isinstance(m, LogMiddleware) for m in middels):
            # Nếu chưa, thêm LogMiddleware vào
            middels.append(Middleware(LogMiddleware))

        return middels




