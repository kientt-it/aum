from pydantic import BaseModel, Field
from typing import List

class ProductItem(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    customer_name: str
    products: List[ProductItem]
    total_amount: float = Field(..., gt=0)

class OrderResponse(BaseModel):
    id: int
    customer_name: str
    total_amount: float


    