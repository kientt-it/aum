import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from odoo.api import Environment
from odoo.exceptions import UserError
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas.user import UserCreate, UserResponse
from typing import Annotated, List
from colorama import Fore, Style, init
from odoo.addons.fastapi_test.middleware.main import LogMiddleware
from datetime import datetime

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
    users = env['res.users'].sudo().search([])

    result = [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            login=user.login if hasattr(user, 'login') else None
        ) for user in users
    ]

    # background_tasks.add_task(LogMiddleware())
    # log_data = request.state.log_data if hasattr(request.state, "log_data") else {}
    # print(log_data)

    return result


@router.post("/users", response_model=UserResponse)
def create_user(
        background_tasks: BackgroundTasks,
        request: Request,
        user_data: UserCreate,
        env: Annotated[Environment, Depends(odoo_env)]
):
    try:
        user = env['res.users'].sudo().create({
            'email': user_data.email,
            'name': user_data.name,
            'login': user_data.login,
        })

        # log_data = request.state.log_data if hasattr(request.state, "log_data") else {}
        # print(log_data)

        return UserResponse(id=user.id, login=user.login, email=user.email, name=user.name)
    except UserError as e:
        log_data = {
            "endpoint": "/users",
            "method": "POST",
            "status_code": 400,
            "error": str(e)
        }
        # print(log_data)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_data = {
            "endpoint": "/users",
            "method": "POST",
            "status_code": 500,
            "error": "Internal Server Error"
        }
        # print(log_data)
        raise HTTPException(status_code=500, detail="Internal Server Error")
