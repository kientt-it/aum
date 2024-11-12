import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from odoo.api import Environment
from odoo.exceptions import UserError
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas.user import UserCreate, UserResponse
from typing import List
import httpx

router = APIRouter()
logger = logging.getLogger("api_logger")

async def send_log_to_odoo(log_data):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8069/api/logs",
                json=log_data,
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        logger.error(f"Failed to send log to Odoo: {e}")

@router.get("/users", response_model=List[UserResponse])
def get_users(
        background_tasks: BackgroundTasks,
        request: Request,
        env: Environment = Depends(odoo_env)
):
    request.state.background_tasks = background_tasks

    users = env['res.users'].sudo().search([])
    result = [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            login=user.login if hasattr(user, 'login') else None
        ) for user in users
    ]

    # Thêm tác vụ ghi log vào background
    background_tasks.add_task(send_log_to_odoo, request.state.log_data)
    return result

@router.post("/users", response_model=UserResponse)
def create_user(
        background_tasks: BackgroundTasks,
        request: Request,
        user_data: UserCreate,
        env: Environment = Depends(odoo_env)
):
    try:
        request.state.background_tasks = background_tasks
        user = env['res.users'].sudo().create({
            'email': user_data.email,
            'name': user_data.name,
            'login': user_data.login,
        })

        # Thêm tác vụ ghi log vào background
        background_tasks.add_task(send_log_to_odoo, request.state.log_data)
        return UserResponse(id=user.id, login=user.login, email=user.email, name=user.name)

    except UserError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
