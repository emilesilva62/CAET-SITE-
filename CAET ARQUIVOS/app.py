from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import secrets
import logging

# Configuração de logging para depuração
logging.basicConfig(level=logging.DEBUG)

# Inicialização do Flask
app = Flask(__name__, static_folder='.')
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Cria a pasta uploads se não existir

# Função para conectar ao banco de dados SQLite
def get_db_connection():
    conn = sqlite3.connect('caet.db')
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn

# Criação da tabela no banco de dados (executa apenas na primeira vez)
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

# Rota para servir o arquivo HTML principal
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Rota para servir arquivos estáticos (CSS, JS)
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
        logging.info('Login bem-sucedido')
        return jsonify({'success': True})
    else:
        logging.warning('Credenciais inválidas ou usuário não encontrado')
        return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401

# Rota para recuperação de senha (simulada)
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

    # Simulação de envio de email (implemente um serviço real em produção)
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