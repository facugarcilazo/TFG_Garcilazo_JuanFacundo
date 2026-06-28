from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import string
import random

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Maneja tanto Clientes como Dueños de Mercado.
    role puede ser 'client' o 'market'
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')
    is_verified = db.Column(db.Boolean, default=False)
    
    # Relaciones
    markets = db.relationship('Market', backref='owner', lazy=True)
    shopping_lists = db.relationship('ShoppingList', backref='user', lazy=True)

class Market(db.Model):
    """
    Detalles del mercado vinculados a un Usuario dueño.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    prices = db.relationship('MarketPrice', backref='market', lazy=True)
    discount_codes = db.relationship('DiscountCode', backref='market', lazy=True)

class Product(db.Model):
    """
    Catálogo global de artículos.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    
    prices = db.relationship('MarketPrice', backref='product', lazy=True)

class MarketPrice(db.Model):
    """
    Tabla de asociación que mapea mercados con productos y precios específicos.
    """
    id = db.Column(db.Integer, primary_key=True)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class ShoppingList(db.Model):
    """
    Lista de productos guardada por el cliente.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    items = db.relationship('ShoppingListItem', backref='shopping_list', lazy=True, cascade="all, delete-orphan")
    discount_codes = db.relationship('DiscountCode', backref='shopping_list', lazy=True)

class ShoppingListItem(db.Model):
    """
    Artículos dentro de una lista de compras.
    """
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    product = db.relationship('Product')

class DiscountCode(db.Model):
    """
    Código único generado cuando se confirma una lista.
    """
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey('shopping_list.id'), nullable=False)
    market_id = db.Column(db.Integer, db.ForeignKey('market.id'), nullable=True)
    discount_percentage = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)
    savings_amount = db.Column(db.Float, default=0.0)
    donation_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
