from collections import OrderedDict
from math import isfinite

from database import get_db
from errors import APIError, ConflictError, NotFoundError
from models.order_model import OrderModel
from models.product_model import ProductModel
from models.user_model import UserModel


ALLOWED_TRANSITIONS = {
    "pendente": {"aprovado", "cancelado"},
    "aprovado": {"enviado", "cancelado"},
    "enviado": {"entregue"},
    "entregue": set(),
    "cancelado": set(),
}


class OrderService:
    def __init__(self):
        self.orders = OrderModel()
        self.products = ProductModel()
        self.users = UserModel()

    def create(self, user_id, raw_items):
        if self.users.find_internal(user_id) is None:
            raise APIError("Usuário não encontrado")
        items = self._validated_items(raw_items)
        connection = get_db()
        try:
            connection.execute("BEGIN IMMEDIATE")
            prepared = []
            total = 0
            for product_id, quantity in items.items():
                product = self.products.find(product_id)
                if product is None:
                    raise APIError(f"Produto {product_id} não encontrado", success=False)
                if product["estoque"] < quantity:
                    raise APIError(f"Estoque insuficiente para {product['nome']}", success=False)
                total += product["preco"] * quantity
                if not isfinite(total):
                    raise APIError('Total do pedido excede o limite numérico')
                prepared.append({
                    "produto_id": product_id,
                    "quantidade": quantity,
                    "preco_unitario": product["preco"],
                })

            order_id = self.orders.create(user_id, total)
            for item in prepared:
                if not self.orders.reduce_stock(item["produto_id"], item["quantidade"]):
                    raise ConflictError("Estoque alterado durante o pedido")
                self.orders.add_item(order_id, item)
            connection.commit()
            return {"pedido_id": order_id, "total": total}
        except Exception:
            connection.rollback()
            raise

    def update_status(self, order_id, new_status):
        if not isinstance(new_status, str) or new_status not in ALLOWED_TRANSITIONS:
            raise APIError("Status inválido")
        connection = get_db()
        try:
            connection.execute("BEGIN IMMEDIATE")
            order = self.orders.find(order_id)
            if order is None:
                raise NotFoundError("Pedido não encontrado")
            if new_status not in ALLOWED_TRANSITIONS[order["status"]]:
                raise ConflictError("Transição de status inválida")
            if new_status == "cancelado":
                self.orders.restore_stock(self.orders.items_for_order(order_id))
            self.orders.update_status(order_id, new_status)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    @staticmethod
    def _validated_items(raw_items):
        if not isinstance(raw_items, list) or not raw_items:
            raise APIError("Pedido deve ter pelo menos 1 item")
        aggregated = OrderedDict()
        for item in raw_items:
            if not isinstance(item, dict):
                raise APIError("Item inválido")
            product_id = item.get("produto_id")
            quantity = item.get("quantidade")
            if isinstance(product_id, bool) or not isinstance(product_id, int):
                raise APIError("Produto ID inválido")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                raise APIError("Quantidade deve ser um inteiro positivo")
            aggregated[product_id] = aggregated.get(product_id, 0) + quantity
        return aggregated
