from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import secrets
import logging
import jwt
import datetime

# Configuração de logging para depuração
logging.basicConfig(level=logging.DEBUG)

# Inicialização do Flask
app = Flask(__name__, static_folder='.')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'sua-chave-secreta'  # Mude para uma chave segura
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Função para conectar ao banco de dados SQLite
def get_db_connection():
    conn = sqlite3.connect('caet.db')
    conn.row_factory = sqlite3.Row
    return conn

# Criação da tabela no banco de dados
with get_db_connection() as conn:
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        dob DATE NOT NULL,
        phone TEXT NOT NULL
    )
    ''')

# Rota para servir o index.html
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Rota para servir o dashboard.html
@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('auth_token')
    if not token:
        return send_from_directory('.', 'index.html')
    try:
        jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return send_from_directory('.', 'dashboard.html')
    except jwt.InvalidTokenError:
        return send_from_directory('.', 'index.html')

# Rota para servir arquivos estáticos (CSS, JS, uploads)
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

# Rota para cadastro de usuário
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    dob = data.get('dob')
    phone = data.get('phone')
    csrf_token = data.get('csrf_token')

    logging.debug(f'Recebido cadastro: name={name}, email={email}, csrf_token={csrf_token}')

    if not csrf_token or not secrets.compare_digest(csrf_token, 'mock-csrf-token'):
        return jsonify({'success': False, 'message': 'CSRF inválido'}), 400

    if not all([name, email, password, dob, phone]):
        return jsonify({'success': False, 'message': 'Campos obrigatórios ausentes'}), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db_connection() as conn:
            conn.execute('INSERT INTO users (name, email, password_hash, dob, phone) VALUES (?, ?, ?, ?, ?)',
                         (name, email, password_hash, dob, phone))
            conn.commit()
        logging.info('Usuário cadastrado com sucesso')
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        logging.warning('Email já cadastrado')
        return jsonify({'success': False, 'message': 'Email já cadastrado'}), 400
    except Exception as e:
        logging.error(f'Erro no cadastro: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# Rota para login de usuário
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    csrf_token = data.get('csrf_token')

    logging.debug(f'Recebido login: email={email}, password={password}, csrf_token={csrf_token}')

    if not csrf_token or not secrets.compare_digest(csrf_token, 'mock-csrf-token'):
        logging.warning('CSRF inválido')
        return jsonify({'success': False, 'message': 'CSRF inválido'}), 400

    if not all([email, password]):
        logging.warning('Campos obrigatórios ausentes')
        return jsonify({'success': False, 'message': 'Campos obrigatórios ausentes'}), 400

    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        logging.debug(f'Usuário encontrado: {user}')

    if user and check_password_hash(user['password_hash'], password):
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        response = jsonify({'success': True})
        response.set_cookie('auth_token', token, httponly=True, secure=True)
        logging.info('Login bem-sucedido')
        return response
    else:
        logging.warning('Credenciais inválidas ou usuário não encontrado')
        return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401

# Rota para login com Google
@app.route('/google-login', methods=['POST'])
def google_login():
    data = request.json
    token = data.get('token')
    logging.debug(f'Recebido Google login: token={token}')
    try:
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE email = ?', ('google-user@example.com',)).fetchone()
            if not user:
                conn.execute('INSERT INTO users (name, email, password_hash, dob, phone) VALUES (?, ?, ?, ?, ?)',
                             ('Google User', 'google-user@example.com', 'google-auth', '2000-01-01', '1234567890'))
                conn.commit()
                user = conn.execute('SELECT * FROM users WHERE email = ?', ('google-user@example.com',)).fetchone()
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        response = jsonify({'success': True})
        response.set_cookie('auth_token', token, httponly=True, secure=True)
        return response
    except Exception as e:
        logging.error(f'Erro no login com Google: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# Rota para logout
@app.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'success': True})
    response.delete_cookie('auth_token')
    return response

# Rota para recuperar perfil do usuário
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    token = request.cookies.get('auth_token')
    if not token:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Token inválido'}), 401

    if request.method == 'GET':
        with get_db_connection() as conn:
            user = conn.execute('SELECT name, email, dob, phone FROM users WHERE id = ?', (user_id,)).fetchone()
            if user:
                return jsonify({'success': True, 'user': dict(user)})
            else:
                return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404

    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        dob = data.get('dob')
        csrf_token = data.get('csrf_token')

        if not csrf_token or not secrets.compare_digest(csrf_token, 'mock-csrf-token'):
            return jsonify({'success': False, 'message': 'CSRF inválido'}), 400

        if not all([name, phone, dob]):
            return jsonify({'success': False, 'message': 'Campos obrigatórios ausentes'}), 400

        try:
            with get_db_connection() as conn:
                conn.execute('UPDATE users SET name = ?, phone = ?, dob = ? WHERE id = ?',
                             (name, phone, dob, user_id))
                conn.commit()
            return jsonify({'success': True})
        except Exception as e:
            logging.error(f'Erro ao atualizar perfil: {str(e)}')
            return jsonify({'success': False, 'message': str(e)}), 500

# Rota para listar arquivos do usuário
@app.route('/files', methods=['GET'])
def list_files():
    token = request.cookies.get('auth_token')
    if not token:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    try:
        jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Token inválido'}), 401

    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            files.append({
                'name': filename,
                'type': 'image/jpeg' if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) else 'application/octet-stream'
            })
    return jsonify({'success': True, 'files': files})

# Rota para recuperação de senha
@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    csrf_token = data.get('csrf_token')

    logging.debug(f'Recebido forgot-password: email={email}, csrf_token={csrf_token}')

    if not csrf_token or not secrets.compare_digest(csrf_token, 'mock-csrf-token'):
        return jsonify({'success': False, 'message': 'CSRF inválido'}), 400

    if not email:
        return jsonify({'success': False, 'message': 'Email obrigatório'}), 400

    return jsonify({'success': True, 'message': 'Email de recuperação enviado'})

# Rota para upload de arquivos
@app.route('/upload', methods=['POST'])
def upload():
    csrf_token = request.form.get('csrf_token')
    logging.debug(f'Recebido upload: csrf_token={csrf_token}')

    if not csrf_token or not secrets.compare_digest(csrf_token, 'mock-csrf-token'):
        return jsonify({'success': False, 'message': 'CSRF inválido'}), 400

    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400

    files = request.files.getlist('files')
    for file in files:
        if file.filename:
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)