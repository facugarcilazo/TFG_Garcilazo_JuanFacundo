import json
import urllib.request
from datetime import datetime
from sqlalchemy import event
from models import (
    db,
    User,
    Market,
    Product,
    MarketPrice,
    ShoppingList,
    ShoppingListItem,
    DiscountCode,
)

# URL de Firebase Realtime Database para persistencia en la nube (nodo separado /maipu_ahorra)
FIREBASE_DB_URL = "https://nursing-dictionary-808e3-default-rtdb.firebaseio.com"
FIREBASE_NODE = "maipu_ahorra"

_is_restoring = False


def _parse_dt(val):
    if not val:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return datetime.utcnow()


def export_db_to_dict():
    """Serializa todas las tablas de SQLite a un diccionario JSON para Firebase."""
    return {
        "updated_at": datetime.utcnow().isoformat(),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "password": u.password,
                "role": u.role,
                "is_verified": bool(u.is_verified),
            }
            for u in User.query.order_by(User.id).all()
        ],
        "markets": [
            {
                "id": m.id,
                "name": m.name,
                "address": m.address,
                "user_id": m.user_id,
            }
            for m in Market.query.order_by(Market.id).all()
        ],
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "image_url": p.image_url,
            }
            for p in Product.query.order_by(Product.id).all()
        ],
        "market_prices": [
            {
                "id": mp.id,
                "market_id": mp.market_id,
                "product_id": mp.product_id,
                "price": mp.price,
                "stock": getattr(mp, "stock", 100),
                "last_updated": mp.last_updated.isoformat() if mp.last_updated else None,
            }
            for mp in MarketPrice.query.order_by(MarketPrice.id).all()
        ],
        "shopping_lists": [
            {
                "id": sl.id,
                "user_id": sl.user_id,
                "name": sl.name,
                "created_at": sl.created_at.isoformat() if sl.created_at else None,
            }
            for sl in ShoppingList.query.order_by(ShoppingList.id).all()
        ],
        "shopping_list_items": [
            {
                "id": item.id,
                "list_id": item.list_id,
                "product_id": item.product_id,
                "quantity": item.quantity,
            }
            for item in ShoppingListItem.query.order_by(ShoppingListItem.id).all()
        ],
        "discount_codes": [
            {
                "id": dc.id,
                "code": dc.code,
                "user_id": dc.user_id,
                "list_id": dc.list_id,
                "market_id": dc.market_id,
                "discount_percentage": dc.discount_percentage,
                "created_at": dc.created_at.isoformat() if dc.created_at else None,
                "used": bool(dc.used),
                "savings_amount": dc.savings_amount,
                "donation_amount": dc.donation_amount,
                "total_amount": dc.total_amount,
            }
            for dc in DiscountCode.query.order_by(DiscountCode.id).all()
        ],
    }


def push_to_firebase():
    """Envía el estado completo de SQLite a Firebase Realtime Database."""
    if not FIREBASE_DB_URL or _is_restoring:
        return False
    try:
        payload = export_db_to_dict()
        data_bytes = json.dumps(payload).encode("utf-8")
        url = f"{FIREBASE_DB_URL}/{FIREBASE_NODE}.json"
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.status == 200
    except Exception as exc:
        print(f"[Firebase Sync] Aviso: No se pudo respaldar en la nube ({exc})")
        return False


def pull_from_firebase():
    """Descarga los datos respaldados en Firebase y sincroniza SQLite al iniciar la app."""
    global _is_restoring
    if not FIREBASE_DB_URL:
        return False

    try:
        url = f"{FIREBASE_DB_URL}/{FIREBASE_NODE}.json"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status != 200:
                return False
            raw = resp.read().decode("utf-8")
            cloud_data = json.loads(raw) if raw else None
    except Exception as exc:
        print(f"[Firebase Sync] Aviso: Sin conexión inicial a Firebase ({exc})")
        return False

    # Si no hay respaldo en la nube todavía, subimos la base de datos local actual
    if not cloud_data or not isinstance(cloud_data, dict) or not cloud_data.get("products"):
        if Product.query.count() > 0:
            push_to_firebase()
        return False

    _is_restoring = True
    try:
        # Sincronizar Usuarios
        for u_data in cloud_data.get("users", []):
            if not u_data:
                continue
            user = User.query.get(u_data["id"])
            if not user:
                user = User(id=u_data["id"])
                db.session.add(user)
            user.username = u_data["username"]
            user.email = u_data["email"]
            user.password = u_data["password"]
            user.role = u_data.get("role", "client")
            user.is_verified = bool(u_data.get("is_verified", False))

        # Sincronizar Mercados
        for m_data in cloud_data.get("markets", []):
            if not m_data:
                continue
            market = Market.query.get(m_data["id"])
            if not market:
                market = Market(id=m_data["id"])
                db.session.add(market)
            market.name = m_data["name"]
            market.address = m_data["address"]
            market.user_id = m_data["user_id"]

        # Sincronizar Productos
        for p_data in cloud_data.get("products", []):
            if not p_data:
                continue
            prod = Product.query.get(p_data["id"])
            if not prod:
                prod = Product(id=p_data["id"])
                db.session.add(prod)
            prod.name = p_data["name"]
            prod.category = p_data["category"]
            prod.image_url = p_data.get("image_url")

        # Sincronizar Precios y Stock de Mercados
        for mp_data in cloud_data.get("market_prices", []):
            if not mp_data:
                continue
            mp = MarketPrice.query.get(mp_data["id"])
            if not mp:
                mp = MarketPrice(id=mp_data["id"])
                db.session.add(mp)
            mp.market_id = mp_data["market_id"]
            mp.product_id = mp_data["product_id"]
            mp.price = float(mp_data["price"])
            mp.stock = int(mp_data.get("stock", 100))
            mp.last_updated = _parse_dt(mp_data.get("last_updated"))

        # Sincronizar Listas de Compras
        for sl_data in cloud_data.get("shopping_lists", []):
            if not sl_data:
                continue
            sl = ShoppingList.query.get(sl_data["id"])
            if not sl:
                sl = ShoppingList(id=sl_data["id"])
                db.session.add(sl)
            sl.user_id = sl_data["user_id"]
            sl.name = sl_data["name"]
            sl.created_at = _parse_dt(sl_data.get("created_at"))

        # Sincronizar Ítems de Listas de Compras
        cloud_items = [i for i in cloud_data.get("shopping_list_items", []) if i]
        cloud_item_ids = {i["id"] for i in cloud_items}
        for existing_item in ShoppingListItem.query.all():
            if existing_item.id not in cloud_item_ids:
                db.session.delete(existing_item)
        for item_data in cloud_items:
            item = ShoppingListItem.query.get(item_data["id"])
            if not item:
                item = ShoppingListItem(id=item_data["id"])
                db.session.add(item)
            item.list_id = item_data["list_id"]
            item.product_id = item_data["product_id"]
            item.quantity = int(item_data.get("quantity", 1))

        # Sincronizar Códigos de Descuento
        for dc_data in cloud_data.get("discount_codes", []):
            if not dc_data:
                continue
            dc = DiscountCode.query.get(dc_data["id"])
            if not dc:
                dc = DiscountCode(id=dc_data["id"])
                db.session.add(dc)
            dc.code = dc_data["code"]
            dc.user_id = dc_data["user_id"]
            dc.list_id = dc_data["list_id"]
            dc.market_id = dc_data.get("market_id")
            dc.discount_percentage = float(dc_data.get("discount_percentage", 10.0))
            dc.created_at = _parse_dt(dc_data.get("created_at"))
            dc.used = bool(dc_data.get("used", False))
            dc.savings_amount = float(dc_data.get("savings_amount", 0.0))
            dc.donation_amount = float(dc_data.get("donation_amount", 0.0))
            dc.total_amount = float(dc_data.get("total_amount", 0.0))

        db.session.commit()
        print("[Firebase Sync] Datos sincronizados desde Firebase Realtime Database.")
        return True
    except Exception as exc:
        db.session.rollback()
        print(f"[Firebase Sync] Error restaurando datos desde Firebase: {exc}")
        return False
    finally:
        _is_restoring = False


def init_firebase_sync(app):
    """Registra el hook automático después de cada commit y sincroniza al iniciar."""
    @event.listens_for(db.session, "after_commit")
    def _after_commit(session):
        if not _is_restoring:
            push_to_firebase()

    with app.app_context():
        pull_from_firebase()
