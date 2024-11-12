import uuid
import logging

import httpx
from fastapi import Request
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from fastapi.exceptions import HTTPException

from odoo.tools.safe_eval import json

import logging
import os

# Ghi log vào file
log_file_path = os.path.join(os.path.dirname(__file__), "G:/Github/AUM/api_logs.log")
logger = logging.getLogger("api_logger")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()

        # Thu thập thông tin request
        request_data = {
            "method": request.method,
            "endpoint": request.url.path,
            "url": str(request.url),
            "path_params": request.path_params,
            "cookies": request.cookies
        }

        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                request_body = await request.json()
            except Exception:
                request_body = await request.body()
            request_data["body"] = request_body

        # Tạo request_id
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Gọi endpoint và xử lý các lỗi có thể xảy ra
        try:
            response = await call_next(request)
            status_code = response.status_code
            response_body = [section async for section in response.body_iterator]
            response_content = b"".join(response_body)
            response_data = {
                "status_code": status_code,
                "headers": dict(response.headers),
                "body": response_content.decode("utf-8") if response_content else "No content"
            }
        except HTTPException as exc:
            # Xử lý các lỗi HTTPException và ghi log
            status_code = exc.status_code
            response_data = {
                "status_code": status_code,
                "error": str(exc.detail)
            }
            response_content = json.dumps(response_data)
            response = JSONResponse(content=response_data, status_code=status_code)
        except Exception as exc:
            # Xử lý các lỗi khác và ghi log
            status_code = 500
            response_data = {
                "status_code": status_code,
                "error": "Internal Server Error",
                "detail": str(exc)
            }
            response_content = json.dumps(response_data)
            response = JSONResponse(content=response_data, status_code=status_code)

        # Tính thời gian xử lý
        process_time = (datetime.now() - start_time).total_seconds()

        # Ghi lại thông tin log bao gồm cả lỗi
        log_data = {
            "process_time": process_time,
            "request": request_data,
            "response": response_data,
        }
        logger.info(log_data)

        # Gửi log_data đến Odoo
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8069/api/logs",
                    json=log_data,
                    headers={"Content-Type": "application/json"}
                )
        except Exception as e:
            logger.error(f"Failed to send log to Odoo: {e}")

        # Trả lại response đã tạo hoặc đã chỉnh sửa
        return Response(
            content=response_content,
            status_code=status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
