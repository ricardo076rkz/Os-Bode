from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from Models import Usuario


def validate_usuario(email, senha, perfil):
    if not email or not senha or not perfil:
        raise ValueError("Email, senha e perfil são obrigatórios.")
    if perfil not in ['cliente', 'lojista']:
        raise ValueError("Perfil deve ser 'cliente' ou 'lojista'.")
    if len(senha) < 6:
        raise ValueError("Senha deve ter pelo menos 6 caracteres.")
    if '@' not in email or '.' not in email:
        raise ValueError("Email inválido.")
    if check_password_hash(senha, generate_password_hash(senha)):
        return Usuario
    return None