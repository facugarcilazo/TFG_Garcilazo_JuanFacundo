from flask import Flask
from models import db
from flask_login import LoginManager, login_required, current_user
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'neon-market-secret-key-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configuración de Flask-Mail (Modo simulado por defecto para evitar errores si no hay credenciales)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'tu_correo@gmail.com' # Reemplazar con credenciales reales
    app.config['MAIL_PASSWORD'] = 'tu_contraseña'       # Reemplazar con credenciales reales
    app.config['MAIL_SUPPRESS_SEND'] = True # Puesto en True para que solo imprima en consola (evita fallo sin credenciales)
    
    from flask_mail import Mail
    mail = Mail()
    mail.init_app(app)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # Registrar blueprints cuando se crean
    from auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    @app.route('/market')
    @login_required
    def market_dashboard():
        from flask import render_template
        if current_user.role != 'market':
            from flask import redirect, url_for, flash
            return redirect(url_for('index'))
            
        from models import Product, MarketPrice, DiscountCode
        all_products = Product.query.all()
        
        # la lógica de mercado asume que el usuario tiene un mercado asociado
        market = current_user.markets[0]
        market_prices = MarketPrice.query.filter_by(market_id=market.id).all()
        
        # --- BI METRICS ---
        from datetime import datetime
        current_month = datetime.utcnow().month
        
        codes = DiscountCode.query.filter_by(market_id=market.id).all()
        
        total_won_lists = len(codes)
        total_potential_revenue = sum(c.total_amount for c in codes)
        unique_clients = len(set(c.user_id for c in codes))
        
        # Monthly stats
        monthly_codes = [c for c in codes if c.created_at.month == current_month]
        monthly_won_lists = len(monthly_codes)
        monthly_revenue = sum(c.total_amount for c in monthly_codes)
        monthly_unique_clients = len(set(c.user_id for c in monthly_codes))
        
        bi_stats = {
            'total_won_lists': total_won_lists,
            'total_revenue': total_potential_revenue,
            'unique_clients': unique_clients,
            'monthly_won_lists': monthly_won_lists,
            'monthly_revenue': monthly_revenue,
            'monthly_unique_clients': monthly_unique_clients
        }
        
        return render_template('panel_mercado.html', all_products=all_products, market_prices=market_prices, bi_stats=bi_stats)

    @app.route('/market/update_price', methods=['POST'])
    @login_required
    def market_update_price():
        from flask import request, redirect, url_for, flash
        if current_user.role != 'market':
            return redirect(url_for('index'))
            
        product_id = request.form.get('product_id')
        price = request.form.get('price')
        
        from models import MarketPrice
        market = current_user.markets[0]
        
        # comprobar si el precio ya existe
        mp = MarketPrice.query.filter_by(market_id=market.id, product_id=product_id).first()
        if mp:
            mp.price = float(price)
            from datetime import datetime
            mp.last_updated = datetime.utcnow()
        else:
            new_price = MarketPrice(market_id=market.id, product_id=product_id, price=float(price))
            db.session.add(new_price)
            
        db.session.commit()
        flash('Precio actualizado correctamente', 'success')
        return redirect(url_for('market_dashboard'))

    @app.route('/client')
    @login_required
    def client_home():
        from flask import render_template, redirect, url_for
        if current_user.role != 'client':
            return redirect(url_for('index'))
            
        from models import DiscountCode
        from datetime import datetime
        current_month = datetime.utcnow().month
        
        codes = DiscountCode.query.filter_by(user_id=current_user.id).all()
        
        monthly_savings = 0.0
        total_donated = 0.0
        total_km_saved = 0
        total_time_saved = 0
        
        for code in codes:
            if code.created_at.month == current_month:
                monthly_savings += code.savings_amount
                total_donated += code.donation_amount
                total_km_saved += 5
                total_time_saved += 30
                
        return render_template('cliente_inicio.html', 
                               monthly_savings=monthly_savings,
                               total_km_saved=total_km_saved,
                               total_time_saved=total_time_saved,
                               total_donated=total_donated)

    @app.route('/client/orders')
    @login_required
    def client_orders():
        from flask import render_template, redirect, url_for
        if current_user.role != 'client':
            return redirect(url_for('index'))
            
        from models import DiscountCode
        discount_codes = DiscountCode.query.filter_by(user_id=current_user.id).order_by(DiscountCode.created_at.desc()).all()
        return render_template('cliente_pedidos.html', discount_codes=discount_codes)

    @app.route('/client/shop')
    @login_required
    def client_shop():
        from flask import render_template, request, redirect, url_for, flash
        if current_user.role != 'client':
            return redirect(url_for('index'))
            
        from models import Product, ShoppingList, DiscountCode, Market, MarketPrice
        q = request.args.get('q', '')
        
        if q:
            products = Product.query.filter(Product.name.ilike(f'%{q}%') | Product.category.ilike(f'%{q}%')).all()
        else:
            products = Product.query.all()
            
        # Obtener o crear lista de compras activa (la que aún no ha sido confirmada por un código de descuento)
        active_list = ShoppingList.query.filter_by(user_id=current_user.id).order_by(ShoppingList.id.desc()).first()
        if not active_list or len(active_list.discount_codes) > 0:
            active_list = ShoppingList(user_id=current_user.id, name="Mi Lista")
            db.session.add(active_list)
            db.session.commit()
            
        # Lógica de comparación: sumar totales por mercado
        market_totals = []
        if active_list.items:
            markets = Market.query.all()
            for m in markets:
                total = 0
                has_all_items = True
                for item in active_list.items:
                    mp = MarketPrice.query.filter_by(market_id=m.id, product_id=item.product_id).first()
                    if mp:
                        total += mp.price * item.quantity
                    else:
                        has_all_items = False
                        break
                if has_all_items:
                    market_totals.append({'market_name': m.name, 'total': total})
            
            # Ordenar por el más barato
            market_totals.sort(key=lambda x: x['total'])
            
        return render_template('cliente_tienda.html', 
                               products=products, 
                               active_list=active_list, 
                               market_totals=market_totals)

    @app.route('/client/add', methods=['POST'])
    @login_required
    def client_add_to_list():
        from flask import request, redirect, url_for, flash
        if current_user.role != 'client':
            return redirect(url_for('index'))
            
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        
        from models import ShoppingList, ShoppingListItem
        active_list = ShoppingList.query.filter_by(user_id=current_user.id).order_by(ShoppingList.id.desc()).first()
        
        # Comprobar si el artículo existe en la lista
        existing_item = ShoppingListItem.query.filter_by(list_id=active_list.id, product_id=product_id).first()
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = ShoppingListItem(list_id=active_list.id, product_id=product_id, quantity=quantity)
            db.session.add(new_item)
            
        db.session.commit()
        flash('Producto agregado a la lista!', 'success')
        return redirect(url_for('client_shop'))

    @app.route('/client/remove/<int:item_id>', methods=['POST'])
    @login_required
    def client_remove_item(item_id):
        from flask import redirect, url_for
        from models import ShoppingListItem
        item = ShoppingListItem.query.get(item_id)
        if item and item.shopping_list.user_id == current_user.id:
            db.session.delete(item)
            db.session.commit()
        return redirect(url_for('client_shop'))

    @app.route('/client/confirm', methods=['POST'])
    @login_required
    def client_confirm_list():
        from flask import redirect, url_for, flash, request
        from models import ShoppingList, DiscountCode, Market, MarketPrice
        import string
        import random
        
        active_list = ShoppingList.query.filter_by(user_id=current_user.id).order_by(ShoppingList.id.desc()).first()
        if active_list and active_list.items:
            # Calcular ahorros
            markets = Market.query.all()
            totals = []
            for m in markets:
                t = 0
                has_all = True
                for item in active_list.items:
                    mp = MarketPrice.query.filter_by(market_id=m.id, product_id=item.product_id).first()
                    if mp:
                        t += mp.price * item.quantity
                    else:
                        has_all = False
                        break
                if has_all:
                    totals.append({'market_id': m.id, 'total': t})
            
            savings = 0.0
            cheapest_total = min([x['total'] for x in totals]) if totals else 0.0
            cheapest_market_id = next((x['market_id'] for x in totals if x['total'] == cheapest_total), None)
            
            if len(totals) >= 2:
                savings = max([x['total'] for x in totals]) - min([x['total'] for x in totals])
                
            # Generar código de descuento
            code_str = 'NEON-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            new_code = DiscountCode(
                code=code_str, 
                user_id=current_user.id, 
                list_id=active_list.id, 
                market_id=cheapest_market_id,
                discount_percentage=10.0, 
                savings_amount=savings,
                total_amount=cheapest_total
            )
            db.session.add(new_code)
            db.session.commit()
            flash(f'¡Lista confirmada! Tu código es {code_str}', 'success')
            return redirect(url_for('client_view_code', code_id=new_code.id))
            
        return redirect(url_for('client_shop'))

    @app.route('/client/code/<int:code_id>')
    @login_required
    def client_view_code(code_id):
        from flask import render_template, redirect, url_for
        from models import DiscountCode
        code = DiscountCode.query.get_or_404(code_id)
        if code.user_id != current_user.id:
            return redirect(url_for('client_home'))
            
        return render_template('codigo_descuento.html', code=code)

    @app.route('/client/donate/<int:code_id>', methods=['POST'])
    @login_required
    def client_donate(code_id):
        from flask import redirect, url_for, flash, request
        from models import DiscountCode
        code = DiscountCode.query.get_or_404(code_id)
        if code.user_id != current_user.id:
            return redirect(url_for('client_home'))
            
        donation_type = request.form.get('donation_type')
        if donation_type == 'savings':
            code.donation_amount = code.savings_amount
        elif donation_type == 'custom':
            custom_amount = request.form.get('custom_amount', 0.0, type=float)
            code.donation_amount = custom_amount
            
        db.session.commit()
        flash(f'¡Gracias por tu donación de ${code.donation_amount:.2f}!', 'success')
        return redirect(url_for('client_home'))

    with app.app_context():
        from models import User, Market, Product, MarketPrice, ShoppingList, ShoppingListItem, DiscountCode
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
