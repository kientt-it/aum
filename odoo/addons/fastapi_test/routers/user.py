from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from odoo.api import Environment
from odoo.exceptions import UserError
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas.user import UserCreate, UserResponse
from typing import List
from colorama import Fore, Style, init

# Khởi tạo APIRouter
router = APIRouter()

# Khởi tạo colorama
init()

@router.get("/users", response_model=List[UserResponse])
def get_users(
        background_tasks: BackgroundTasks,
        request: Request,
        env: Environment = Depends(odoo_env)
):
    # Truyền `background_tasks` vào `request.state`
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
    return result


@router.post("/users", response_model=UserResponse)
def create_user(
        background_tasks: BackgroundTasks,
        request: Request,
        user_data: UserCreate,
        env: Environment = Depends(odoo_env)
):
    try:
        # Truyền `background_tasks` vào `request.state`
        request.state.background_tasks = background_tasks

        # Tạo người dùng mới
        user = env['res.users'].sudo().create({
            'email': user_data.email,
            'name': user_data.name,
            'login': user_data.login,
        })

        return UserResponse(id=user.id, login=user.login, email=user.email, name=user.name)

    except UserError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
