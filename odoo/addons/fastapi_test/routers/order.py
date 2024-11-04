from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from odoo.api import Environment
from odoo.exceptions import UserError
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas.order import OrderCreate, OrderResponse

router = APIRouter()

@router.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    env: Annotated[Environment, Depends(odoo_env)]
):
    try:
        # Tạo khách hàng mới hoặc tìm khách hàng hiện có
        partner = env['res.partner'].search([('name', '=', order_data.customer_name)], limit=1)
        if not partner:
            partner = env['res.partner'].create({'name': order_data.customer_name})

        # Tạo đơn hàng
        order = env['sale.order'].create({
            'partner_id': partner.id,
            'amount_total': order_data.total_amount,
        })

        # Thêm các sản phẩm vào đơn hàng
        for item in order_data.products:
            env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': item.product_id,
                'product_uom_qty': item.quantity,
            })

        return OrderResponse(
            id=order.id,
            customer_name=order.partner_id.name,
            total_amount=order.amount_total
        )
    except UserError as e:
        raise HTTPException(status_code=400, detail=str(e))

