from app import app, db
from models import Product, User, Market, MarketPrice
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        import random
        catalog = [
            ("Leche Entera 1L", "Lácteos", "imagenes/productos/leche.jpg"),
            ("Pan de Molde", "Panadería", "imagenes/productos/pan.jpg"),
            ("Huevos Docena", "Lácteos", "imagenes/productos/huevos.jpg"),
            ("Coca Cola 2L", "Bebidas", "imagenes/productos/coca.jpg"),
            ("Arroz 1kg", "Despensa", "imagenes/productos/arroz.jpg"),
            ("Fideos Spaghetti 500g", "Despensa", "imagenes/productos/fideos.jpg"),
            ("Detergente Liquido 3L", "Limpieza", "imagenes/productos/detergente.jpg"),
            ("Papel Higiénico 4u", "Limpieza", "imagenes/productos/papel.jpg"),
            ("Manzanas 1kg", "Frutas", "imagenes/productos/manzanas.jpg"),
            ("Carne Picada 1kg", "Carnicería", "imagenes/productos/carne.jpg"),
            ("Yerba Mate 1kg", "Despensa", "imagenes/productos/yerba.jpg"),
            ("Aceite de Girasol 1.5L", "Despensa", "imagenes/productos/aceite.jpg"),
            ("Harina de Trigo 000 1kg", "Despensa", "imagenes/productos/harina.jpg"),
            ("Azúcar Blanca 1kg", "Despensa", "imagenes/productos/azucar.jpg"),
            ("Dulce de Leche 400g", "Lácteos", "imagenes/productos/dulce_de_leche.jpg"),
            ("Queso Cremoso 1kg", "Lácteos", "imagenes/productos/queso_cremoso.jpg"),
            ("Pollo Entero 1kg", "Carnicería", "imagenes/productos/pollo.jpg"),
            ("Asado de Tira 1kg", "Carnicería", "imagenes/productos/asado.jpg"),
            ("Puré de Tomate 520g", "Despensa", "imagenes/productos/pure_tomate.jpg"),
            ("Galletitas de Agua 300g", "Panadería", "imagenes/productos/galletitas.jpg"),
            ("Papa Negra 1kg", "Verdulería", "imagenes/productos/papa.jpg"),
            ("Lavandina 1L", "Limpieza", "imagenes/productos/lavandina.jpg")
        ]

        added_products = 0
        for name, category, image_url in catalog:
            existing = Product.query.filter_by(name=name).first()
            if not existing:
                db.session.add(Product(name=name, category=category, image_url=image_url))
                added_products += 1
            else:
                existing.image_url = image_url
        db.session.commit()
        if added_products > 0:
            print(f"Se agregaron {added_products} productos nuevos al catálogo.")

        if User.query.filter_by(email='mercadoeco+@prueba.com').count() == 0:
            print("Seeding sample markets...")
            hashed_pw = generate_password_hash('12345', method='pbkdf2:sha256')
            
            # Mercado Eco+
            market_user1 = User(username='mercadoeco+', email='mercadoeco+@prueba.com', password=hashed_pw, role='market', is_verified=True)
            db.session.add(market_user1)
            
            # Mercado Toto
            market_user2 = User(username='mercadototo', email='mercadototo@prueba.com', password=hashed_pw, role='market', is_verified=True)
            db.session.add(market_user2)
            
            db.session.commit()
            
            market1 = Market(name="Mercado Eco+", address="Av. Central 456", owner=market_user1)
            market2 = Market(name="Mercado Toto", address="Calle Principal 789", owner=market_user2)
            db.session.add_all([market1, market2])
            db.session.commit()
            print("Sample Markets created! (passwords: 12345)")

        # Asegurar que todos los mercados tengan precios para todos los productos del catálogo
        all_markets = Market.query.all()
        all_prods = Product.query.all()
        added_prices = 0
        for m in all_markets:
            for p in all_prods:
                mp = MarketPrice.query.filter_by(market_id=m.id, product_id=p.id).first()
                if not mp:
                    db.session.add(MarketPrice(
                        market_id=m.id,
                        product_id=p.id,
                        price=round(random.uniform(800.0, 4500.0), 2)
                    ))
                    added_prices += 1
        db.session.commit()
        if added_prices > 0:
            print(f"Se asignaron {added_prices} precios nuevos en los mercados.")

        if User.query.filter_by(username='cliente1').count() == 0:
            print("Seeding sample client...")
            hashed_pw = generate_password_hash('12345', method='pbkdf2:sha256')
            client_user = User(username='cliente1', email='cliente1@prueba.com', password=hashed_pw, role='client', is_verified=True)
            db.session.add(client_user)
            db.session.commit()
            print("Sample Client created! (user: cliente1@prueba.com / 12345)")

if __name__ == '__main__':
    seed_data()
    print("Seed complete.")
