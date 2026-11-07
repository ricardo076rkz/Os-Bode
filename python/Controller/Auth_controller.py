from flask import Blueprint, jsonify, request
from Service import Auth_service

auth_bp = Blueprint('auth_bp', __name__)
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        senha = data.get('senha')

        if not email or not senha:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400

        token = Auth_service.AuthService.login(email, senha)
        if token:
            return jsonify({'token': token}), 200
        else:
            return jsonify({'error': 'Credenciais inválidas'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 400