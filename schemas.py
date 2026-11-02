from pydantic import BaseModel, Field
from typing import List, Optional


class UserCreate(BaseModel):
    name: str = Field(..., description="Nombre completo del usuario", examples=["Ana López"])
    email: str = Field(..., description="Dirección de correo electrónico única", examples=["ana.lopez@example.com"])


class ProductCreate(BaseModel):
    name: str = Field(..., description="Nombre descriptivo del producto", examples=["Smartphone Pro"])
    price: float = Field(..., description="Precio unitario del producto", examples=[850.00])
    stock: int = Field(..., description="Cantidad de unidades disponibles en inventario", examples=[15])


class OrderCreate(BaseModel):
    user_id: int = Field(..., description="Identificador único del usuario que realiza la compra", examples=[1])
    product_ids: List[int] = Field(..., description="Lista de identificadores de los productos a ordenar (admite unidades repetidas)", examples=[[1, 2, 2]])


