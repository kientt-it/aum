import asyncio
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from odoo.api import Environment
from odoo.addons.fastapi.dependencies import odoo_env
from ..schemas.user import UserCreate, UserResponse
import requests
from typing import List
from datetime import datetime
import httpx

router = APIRouter()
logger = logging.getLogger("api_logger")

# Hàm gửi log tới Odoo
async def send_log_to_odoo(log_data):
    logger.info(f"Preparing to send log: {log_data}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8069/api/logs",
                json=log_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Log sent successfully to Odoo: {log_data}")
        except Exception as e:
            logger.error(f"Failed to send log to Odoo: {e}")

@router.post("/users", response_model=UserResponse)
async def create_user(
        user_data: UserCreate,
        request: Request,
        background_tasks: BackgroundTasks,
        env: Environment = Depends(odoo_env)
):
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    request.state.request_id = request_id

    # Thu thập thông tin request
    request_data = {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "endpoint": request.url.path,
        "cookies": request.cookies,
        "body": user_data.model_dump()
    }

    response_data = {}  # Dữ liệu response mặc định để ghi log
    log_data = {}  # Biến log data toàn cục

    try:
        # Kiểm tra nếu tên đăng nhập đã tồn tại
        existing_user = env['res.users'].sudo().search([('login', '=', user_data.login)], limit=1)
        if existing_user:
            response_data = {
                "status_code": 400,
                "error": "Login already exists"
            }
            log_data = {
                "request": request_data,
                "response": response_data,
                "process_time": (datetime.now() - start_time).total_seconds()
            }
            # Gửi log ngay lập tức khi lỗi xảy ra
            # await send_log_to_odoo(log_data)
            # background_tasks.add_task(send_log_to_odoo, log_data)
            raise HTTPException(status_code=400, detail="Login already exists")

        # Tạo người dùng mới nếu không có lỗi
        user = env['res.users'].sudo().create({
            'email': user_data.email,
            'name': user_data.name,
            'login': user_data.login,
        })

        # Dữ liệu trả về nếu thành công
        response_data = {
            "status_code": 200,
            "data": {
                "id": user.id,
                "login": user.login,
                "email": user.email,
                "name": user.name
            }
        }
        log_data = {
            "request": request_data,
            "response": response_data,
            "process_time": (datetime.now() - start_time).total_seconds()
        }

        # Thêm log vào background tasks
        await send_log_to_odoo(log_data)
        # background_tasks.add_task(send_log_to_odoo, log_data)
        return response_data["data"]

    except HTTPException as http_exc:
        # Ghi log cho lỗi HTTP
        response_data = {
            "status_code": http_exc.status_code,
            "error": http_exc.detail
        }
        log_data = {
            "request": request_data,
            "response": response_data,
            "process_time": (datetime.now() - start_time).total_seconds()
        }
        await send_log_to_odoo(log_data)
        # background_tasks.add_task(send_log_to_odoo, log_data)
        raise http_exc

    except Exception as e:
        # Ghi log cho lỗi không mong đợi
        response_data = {
            "status_code": 500,
            "error": "Internal Server Error",
            "detail": str(e)
        }
        log_data = {
            "request": request_data,
            "response": response_data,
            "process_time": (datetime.now() - start_time).total_seconds()
        }
        await send_log_to_odoo(log_data)
        # background_tasks.add_task(send_log_to_odoo, log_data)
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        # Đảm bảo log được ghi bất kể thành công hay thất bại
        if not log_data:  # Nếu log_data chưa được thiết lập trong các khối trên
            log_data = {
                "request": request_data,
                "response": response_data,
                "process_time": (datetime.now() - start_time).total_seconds()
            }

        background_tasks.add_task(send_log_to_odoo, log_data)
