from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Market

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Por favor, verifica tu correo electrónico antes de iniciar sesión. (Si estás probando, busca el enlace en la consola de ejecución)', 'error')
                return redirect(url_for('auth.login'))
                
            remember = True if request.form.get('remember') else False
            login_user(user, remember=remember)
            flash('Sesión iniciada correctamente', 'success')
            if user.role == 'market':
                return redirect(url_for('market_dashboard'))
            return redirect(url_for('client_home'))
            
        flash('Email o contraseña incorrectos', 'error')
        
    return render_template('iniciar_sesion.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    # 'type' podría ser 'market' o 'client'
    reg_type = request.args.get('type', 'client')
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'client')
        
        # Comprobar si el usuario existe
        user_exists = User.query.filter((User.email == email) | (User.username == username)).first()
        if user_exists:
            flash('El email o nombre de usuario ya está registrado.', 'error')
            return redirect(url_for('auth.register', type=reg_type))
            
        # Crear nuevo usuario
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Si es mercado, también crear el perfil del mercado
        if role == 'market':
            market_name = request.form.get('market_name')
            address = request.form.get('address')
            new_market = Market(name=market_name, address=address, owner=new_user)
            db.session.add(new_market)
            db.session.commit()
        # Generar token de verificación
        from itsdangerous import URLSafeTimedSerializer
        from flask_mail import Message
        from flask import current_app
        import sys
        
        # Necesitamos instanciar mail localmente porque lo creamos en app.py
        # Una forma mejor es tener mail como extensión global en models.py o un extensions.py,
        # pero podemos hacer una importación perezosa temporal de 'mail' para enviar el mensaje.
        
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = s.dumps(email, salt='email-confirm')
        link = url_for('auth.verify_email', token=token, _external=True)
        
        # Enviar correo (O simularlo en consola debido a MAIL_SUPPRESS_SEND=True)
        msg = Message('Verifica tu cuenta en Maipú Ahorra', sender='noreply@maipuahorra.com', recipients=[email])
        msg.body = f'¡Hola {username}!\n\nPor favor, verifica tu cuenta haciendo clic en el siguiente enlace:\n{link}\n\nSi no creaste esta cuenta, ignora este correo.'
        
        try:
            # Requerimos importar app para acceder a 'mail' en este diseño monolítico simple
            from app import mail
            mail.send(msg)
            # Imprimir link en consola para que el desarrollador pueda probar
            print(f"\n[SISTEMA DE CORREO SIMULADO] Email enviado a {email}:\n{msg.body}\n", file=sys.stderr)
        except Exception as e:
            print(f"Error simulando envío: {e}", file=sys.stderr)
            
        flash('Registro exitoso. Te hemos enviado un enlace de verificación a tu correo.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('registro.html', reg_type=reg_type)

@auth_bp.route('/verify/<token>')
def verify_email(token):
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired
    from flask import current_app
    
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        # El token dura 1 hora (3600 segundos)
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('El enlace de verificación ha expirado.', 'error')
        return redirect(url_for('auth.login'))
    except Exception:
        flash('El enlace de verificación es inválido.', 'error')
        return redirect(url_for('auth.login'))
        
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('No se encontró el usuario asociado a este enlace.', 'error')
        return redirect(url_for('auth.register'))
        
    if user.is_verified:
        flash('La cuenta ya estaba verificada. Inicia sesión.', 'success')
    else:
        user.is_verified = True
        db.session.commit()
        flash('¡Cuenta verificada exitosamente! Ahora puedes iniciar sesión.', 'success')
        
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente.', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verificar que el nombre de usuario o email no exista en otro usuario
        existing_user = User.query.filter(
            ((User.email == email) | (User.username == username)) & (User.id != current_user.id)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                flash('Ese correo electrónico ya está en uso por otra cuenta.', 'error')
            else:
                flash('Ese nombre de usuario ya está en uso.', 'error')
            return redirect(url_for('auth.profile'))
            
        current_user.username = username
        current_user.email = email
        
        # Si se completó el campo contraseña, actualizarla
        if password and password.strip():
            current_user.password = generate_password_hash(password, method='pbkdf2:sha256')
            
        db.session.commit()
        flash('Perfil actualizado con éxito.', 'success')
        
        # Redirigir al panel correspondiente
        if current_user.role == 'market':
            return redirect(url_for('market_dashboard'))
        return redirect(url_for('client_home'))
        
    return render_template('perfil.html')
