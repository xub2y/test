from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import os
import os
import os

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    if not password:
        return jsonify({'error': '密码不能为空'}), 400

    # ⚠️ 预埋Bug BUG-001：故意不校验用户名长度>=6位
    # if len(username) < 6:
    #     return jsonify({'error': '用户名长度不能少于6位'}), 400

    if len(username) > 20:
        return jsonify({'error': '用户名长度不能超过20位'}), 400
    if len(password) < 6:
        return jsonify({'error': '密码长度不能少于6位'}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                  (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({'message': '注册成功'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': '该用户名已被注册'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    if not password:
        return jsonify({'error': '密码不能为空'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        token = f"token_{username}_demo"
        return jsonify({'message': '登录成功', 'token': token, 'username': username}), 200
    else:
        return jsonify({'error': '用户名或密码错误'}), 401

@app.route('/api/userinfo', methods=['GET'])
def userinfo():
    token = request.headers.get('Authorization', '')
    if not token.startswith('token_'):
        return jsonify({'error': '未登录'}), 401
    username = token.replace('token_', '').replace('_demo', '')
    return jsonify({'username': username}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
