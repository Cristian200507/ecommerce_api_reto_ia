from fastapi import FastAPI, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
import models, schemas, database

tags_metadata = [
    {
        "name": "Usuarios",
        "description": "Operaciones para la gestión de usuarios y consulta de su historial de pedidos.",
    },
    {
        "name": "Productos",
        "description": "Consulta del catálogo de productos con soporte para paginación.",
    },
    {
        "name": "Pedidos",
        "description": "Procesamiento transaccional de órdenes de compra con control de inventario y promociones.",
    },
]

app = FastAPI(
    title="E-commerce API - Reto IA",
    description=(
        "API RESTful de comercio electrónico desarrollada con FastAPI y SQLAlchemy. "
        "Permite el registro de usuarios, catálogo paginado de productos, procesamiento de pedidos "
        "con control de concurrencia pesimista (with_for_update), cálculo automático de descuentos "
        "y consulta del historial de órdenes."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
)


models.Base.metadata.create_all(bind=database.engine)


def apply_discount(price: float) -> float:
    """Calcula y aplica la regla de descuento sobre el precio de un producto.

    Aplica un 10% de descuento (precio * 0.9) si el precio unitario del producto
    es estrictamente mayor a 100. En caso contrario, mantiene el precio original.

    Args:
        price (float): Precio original del producto.

    Returns:
        float: Precio final tras evaluar la condición de descuento.
    """
    if price > 100:
        return price * 0.9
    return price


@app.post(
    "/users/",
    tags=["Usuarios"],
    summary="Registrar un nuevo usuario",
    description="Crea un usuario en el sistema validando que el correo electrónico no esté registrado previamente.",
    responses={
        200: {
            "description": "Usuario registrado exitosamente.",
            "content": {
                "application/json": {
                    "example": {"id": 1, "name": "Ana López", "email": "ana.lopez@example.com"}
                }
            },
        },
        409: {
            "description": "Conflicto: El correo electrónico ya se encuentra registrado.",
            "content": {
                "application/json": {
                    "example": {"detail": "El correo electrónico ya se encuentra registrado"}
                }
            },
        },
        422: {"description": "Error de validación en la estructura de la solicitud."},
    },
)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """Crea un nuevo usuario en la base de datos previa validación de unicidad de email.

    Args:
        user (schemas.UserCreate): Datos del usuario (nombre y correo electrónico).
        db (Session): Sesión activa de base de datos SQLAlchemy.

    Raises:
        HTTPException: 409 si el correo ya está registrado en el sistema.

    Returns:
        models.User: Entidad del usuario persistido con su ID asignado.
    """
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="El correo electrónico ya se encuentra registrado"
        )
    
    new_user = models.User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get(
    "/users/{user_id}/orders",
    tags=["Usuarios"],
    summary="Consultar historial de pedidos de un usuario",
    description="Obtiene todos los pedidos realizados por un usuario específico empleando carga anticipada para optimizar las consultas.",
    responses={
        200: {
            "description": "Historial de pedidos obtenido exitosamente.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "order_id": 101,
                            "total": 720.0,
                            "products": ["Smartphone Pro"]
                        }
                    ]
                }
            },
        },
        404: {
            "description": "El usuario especificado no existe.",
            "content": {
                "application/json": {
                    "example": {"detail": "Usuario no encontrado"}
                }
            },
        },
    },
)
def get_user_orders(
    user_id: int = Path(..., description="Identificador único del usuario a consultar", examples=[1], ge=1),
    db: Session = Depends(database.get_db)
):
    """Consulta el historial de pedidos de un usuario y retorna los detalles de compra.

    Args:
        user_id (int): Identificador del usuario.
        db (Session): Sesión de base de datos.

    Raises:
        HTTPException: 404 si el usuario no existe.

    Returns:
        List[Dict[str, Any]]: Lista de pedidos con order_id, total y nombres de productos.
    """
    user = (
        db.query(models.User)
        .options(joinedload(models.User.orders))
        .filter(models.User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    orders_data = []
    for order in user.orders:
        products = getattr(order, "products", None)
        if products is not None:
            product_names = [p.name if hasattr(p, "name") else str(p) for p in products]
        elif hasattr(order, "items"):
            product_names = [
                item.product.name if hasattr(item, "product") and hasattr(item.product, "name")
                else (item.name if hasattr(item, "name") else str(item))
                for item in order.items
            ]
        else:
            product_names = []

        orders_data.append({
            "order_id": order.id,
            "total": order.total_price,
            "products": product_names
        })
    
    return orders_data


@app.get(
    "/products/",
    tags=["Productos"],
    summary="Listar productos con paginación",
    description="Retorna el catálogo de productos disponibles utilizando los parámetros limit y offset para paginación controlada.",
    responses={
        200: {
            "description": "Página de productos obtenida exitosamente.",
            "content": {
                "application/json": {
                    "example": [
                        {"id": 1, "name": "Smartphone Pro", "price": 800.0, "stock": 5},
                        {"id": 2, "name": "Funda Protectora", "price": 20.0, "stock": 10}
                    ]
                }
            },
        },
        422: {"description": "Error en los parámetros de consulta (limit fuera de rango o offset negativo)."},
    },
)
def get_products(
    limit: int = Query(default=10, le=100, ge=1, description="Número máximo de productos a retornar (1 a 100)", examples=[10]),
    offset: int = Query(default=0, ge=0, description="Cantidad de productos a omitir desde el inicio", examples=[0]),
    db: Session = Depends(database.get_db)
):
    """Obtiene una lista paginada de productos del catálogo.

    Args:
        limit (int): Límite de resultados a retornar (1 a 100, predeterminado: 10).
        offset (int): Desplazamiento inicial de la consulta (mínimo: 0, predeterminado: 0).
        db (Session): Sesión de base de datos.

    Returns:
        List[models.Product]: Lista de productos que cumplen con los criterios de paginación.
    """
    return db.query(models.Product).offset(offset).limit(limit).all()


@app.post(
    "/orders/",
    tags=["Pedidos"],
    summary="Procesar una orden de compra",
    description=(
        "Procesa un pedido validando existencia del usuario, bloqueando los registros de productos "
        "con bloqueo pesimista (with_for_update) para evitar condiciones de carrera, verificando stock "
        "suficiente y aplicando un 10% de descuento en productos cuyo valor supere 100."
    ),
    responses={
        200: {
            "description": "Orden procesada y confirmada exitosamente.",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "order_id": 1, "total": 740.0}
                }
            },
        },
        400: {
            "description": "Solicitud inválida: Producto inexistente o existencias de stock insuficientes.",
            "content": {
                "application/json": {
                    "examples": {
                        "producto_no_existe": {
                            "summary": "Producto inexistente",
                            "value": {"detail": "Producto 99 no existe"}
                        },
                        "stock_insuficiente": {
                            "summary": "Stock insuficiente",
                            "value": {"detail": "Stock insuficiente para el producto 'Smartphone Pro' (ID: 1)"}
                        }
                    }
                }
            },
        },
        404: {
            "description": "El usuario especificado no existe en la plataforma.",
            "content": {
                "application/json": {
                    "example": {"detail": "Usuario no encontrado"}
                }
            },
        },
        422: {"description": "Error de validación en el cuerpo de la petición."},
    },
)
def process_order(order: schemas.OrderCreate, db: Session = Depends(database.get_db)):
    """Procesa una nueva orden de compra, descuenta inventario y persiste el pedido.

    Args:
        order (schemas.OrderCreate): Datos de la orden (user_id y lista product_ids).
        db (Session): Sesión de base de datos.

    Raises:
        HTTPException: 404 si el usuario no existe.
        HTTPException: 400 si un producto no existe en el catálogo.
        HTTPException: 400 si algún producto no cuenta con existencias suficientes en stock.

    Returns:
        dict: Estado del proceso, identificador de la orden creada y total facturado.
    """
    user = db.query(models.User).filter(models.User.id == order.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    products = (
        db.query(models.Product)
        .filter(models.Product.id.in_(order.product_ids))
        .with_for_update()
        .all()
        if order.product_ids
        else []
    )
    products_by_id = {prod.id: prod for prod in products}

    total = 0
    for pid in order.product_ids:
        prod = products_by_id.get(pid)
        if not prod:
            raise HTTPException(status_code=400, detail=f"Producto {pid} no existe")
        
        if prod.stock <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para el producto '{prod.name}' (ID: {pid})"
            )
        
        precio_final = apply_discount(prod.price)
        
        total += precio_final
        
        prod.stock = prod.stock - 1
        db.add(prod)

    new_order = models.Order(user_id=order.user_id, total_price=total)
    db.add(new_order)
    db.commit()
    return {"status": "ok", "order_id": new_order.id, "total": total}
