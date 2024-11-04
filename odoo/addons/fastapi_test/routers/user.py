from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from odoo.api import Environment
from odoo.exceptions import UserError
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    env: Annotated[Environment, Depends(odoo_env)]
):
    try:
        user = env['res.users'].sudo().create({
            'login': user_data.login,
            'name': user_data.name,
        })
        return UserResponse(id=user.id, login=user.login, name=user.name)
    except UserError as e:
        raise HTTPException(status_code=400, detail=str(e))



