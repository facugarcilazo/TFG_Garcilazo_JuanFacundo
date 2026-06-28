from app import app, db
from models import Product, User, Market, MarketPrice
from werkzeug.security import generate_password_hash

def seed_data():
    with app.app_context():
        # Limpiar actuales (si es necesario, pero usualmente solo agregamos si está vacío)
        if Product.query.count() == 0:
            print("Seeding products...")
            products = [
                Product(name="Leche Entera 1L", category="Lácteos", image_url="imagenes/productos/leche.jpg"),
                Product(name="Pan de Molde", category="Panadería", image_url="imagenes/productos/pan.jpg"),
                Product(name="Huevos Docena", category="Lácteos", image_url="imagenes/productos/huevos.jpg"),
                Product(name="Coca Cola 2L", category="Bebidas", image_url="imagenes/productos/coca.jpg"),
                Product(name="Arroz 1kg", category="Despensa", image_url="imagenes/productos/arroz.jpg"),
                Product(name="Fideos Spaghetti 500g", category="Despensa", image_url="imagenes/productos/fideos.jpg"),
                Product(name="Detergente Liquido 3L", category="Limpieza", image_url="imagenes/productos/detergente.jpg"),
                Product(name="Papel Higiénico 4u", category="Limpieza", image_url="imagenes/productos/papel.jpg"),
                Product(name="Manzanas 1kg", category="Frutas", image_url="imagenes/productos/manzanas.jpg"),
                Product(name="Carne Picada 1kg", category="Carnicería", image_url="imagenes/productos/carne.jpg")
            ]
            db.session.add_all(products)
            db.session.commit()
            print("Products created!")

        if User.query.filter_by(email='mercadoeco+@prueba.com').count() == 0:
            print("Seeding sample markets...")
            hashed_pw = generate_password_hash('12345', method='pbkdf2:sha256')
            
            # Mercado Eco+
            market_user1 = User(username='mercadoeco+', email='mercadoeco+@prueba.com', password=hashed_pw, role='market')
            db.session.add(market_user1)
            
            # Mercado Toto
            market_user2 = User(username='mercadototo', email='mercadototo@prueba.com', password=hashed_pw, role='market')
            db.session.add(market_user2)
            
            db.session.commit()
            
            market1 = Market(name="Mercado Eco+", address="Av. Central 456", owner=market_user1)
            market2 = Market(name="Mercado Toto", address="Calle Principal 789", owner=market_user2)
            db.session.add_all([market1, market2])
            db.session.commit()
            
            # Agregar algunos precios para ambos
            all_prods = Product.query.all()
            import random
            for p in all_prods:
                mp1 = MarketPrice(market_id=market1.id, product_id=p.id, price=round(random.uniform(50.0, 500.0), 2))
                mp2 = MarketPrice(market_id=market2.id, product_id=p.id, price=round(random.uniform(50.0, 500.0), 2))
                db.session.add_all([mp1, mp2])
            db.session.commit()
            print("Sample Markets and prices created! (passwords: 12345)")

        if User.query.filter_by(username='cliente1').count() == 0:
            print("Seeding sample client...")
            hashed_pw = generate_password_hash('12345', method='pbkdf2:sha256')
            client_user = User(username='cliente1', email='cliente1@prueba.com', password=hashed_pw, role='client')
            db.session.add(client_user)
            db.session.commit()
            print("Sample Client created! (user: cliente1@prueba.com / 12345)")

if __name__ == '__main__':
    seed_data()
    print("Seed complete.")
