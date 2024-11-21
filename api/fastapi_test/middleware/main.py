# import uuid
# import logging
#
# import httpx
# from fastapi import Request, BackgroundTasks
# from datetime import datetime
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.responses import JSONResponse, Response
# from fastapi.exceptions import HTTPException
#
# from odoo.addons.fastapi_test.routers.user import send_log_to_odoo
# from odoo.tools.safe_eval import json
#
# import logging
# import os
#
# # Đường dẫn tuyệt đối đến file log
# log_file_path = os.path.join(os.path.dirname(__file__), "G:/aum/api_logs.log")
#
# # Tạo logger
# logger = logging.getLogger("api_logger")
# logger.setLevel(logging.INFO)  # Đặt mức độ log là INFO
#
# # Tạo handler để ghi log vào file
# file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
# file_handler.setLevel(logging.INFO)
#
# # Định dạng log
# formatter = logging.Formatter("%(asctime)s - %(message)s")
# file_handler.setFormatter(formatter)
#
# # Thêm handler vào logger
# logger.addHandler(file_handler)
#
# class LogMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         request_id = request.state.request_id if hasattr(request.state, "request_id") else str(uuid.uuid4())
#         start_time = datetime.now()
#
#         request_data = {
#             "request_id": request_id,
#             "method": request.method,
#             "endpoint": request.url.path,
#             "url": str(request.url),
#             # "headers": dict(request.headers),
#             # "query_params": dict(request.query_params),
#             # "path_params": request.path_params,
#             "cookies": request.cookies
#         }
#
#         if request.method in ["POST", "PUT", "PATCH"]:
#             try:
#                 request_body = await request.json()
#             except Exception:
#                 request_body = await request.body()
#             request_data["body"] = request_body
#
#         response_data = {}
#         # Gọi endpoint và xử lý các lỗi có thể xảy ra
#         try:
#             response = await call_next(request)
#             status_code = response.status_code
#             response_body = [section async for section in response.body_iterator]
#             response_content = b"".join(response_body)
#             response_data = {
#                 "status_code": status_code,
#                 "headers": dict(response.headers),
#                 "body": response_content.decode("utf-8") if response_content else "No content"
#             }
#         except HTTPException as exc:
#             status_code = exc.status_code
#             response_data = {
#                 "status_code": status_code,
#                 "error": str(exc.detail)
#             }
#             response_content = json.dumps(response_data)
#             response = JSONResponse(content=response_data, status_code=status_code)
#         except Exception as exc:
#             status_code = 500
#             response_data = {
#                 "status_code": status_code,
#                 "error": "Internal Server Error",
#                 "detail": str(exc)
#             }
#             response_content = json.dumps(response_data)
#             response = JSONResponse(content=response_data, status_code=status_code)
#
#         finally:
#             process_time = (datetime.now() - start_time).total_seconds()
#
#             # Ghi lại thông tin log bao gồm cả lỗi
#             log_data = {
#                 "process_time": process_time,
#                 "request": request_data,
#                 "response": response_data,
#             }
#
#             logger.info(log_data)
#
#             if hasattr(request.state, "background_tasks"):
#                 background_tasks = request.state.background_tasks
#                 background_tasks.add_task(send_log_to_odoo, log_data)
#             else:
#                 logger.warning("Không tìm thấy BackgroundTasks trong request.state")
#
#         return Response(
#             content=response_content,
#             status_code=status_code,
#             headers=dict(response.headers),
#             media_type=response.media_type
#         )