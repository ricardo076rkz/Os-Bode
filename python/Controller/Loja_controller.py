from flask import Blueprint, jsonify, request
from Models import Loja
from Service import Loja_service

loja_bp = Blueprint('loja_bp', __name__)

@loja_bp.route('/lojas', methods=['GET'])
def get_all_lojas():
    try:
        lojas = Loja_service.LujaService.get_all_lojas()
        return jsonify([loja.__dict__ for loja in lojas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@loja_bp.route('/lojas/<int:loja_id>', methods=['GET'])
def get_loja_by_id(loja_id):
    try:
        loja = Loja_service.LujaService.get_loja_by_id(loja_id)
        if loja:
            return jsonify(loja.__dict__), 200
        else:
            return jsonify({'error': 'Loja não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@loja_bp.route('/lojas', methods=['POST'])
def create_loja():
    try:
        data = request.get_json()
        new_loja = Loja(nome=data['nome'], endereco=data['endereco'])
        created_loja = Loja_service.LujaService.create_loja(new_loja)
        if created_loja:
            return jsonify(created_loja.__dict__), 201
        else:
            return jsonify({'error': 'Erro ao criar loja'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@loja_bp.route('/lojas/<int:loja_id>', methods=['PUT'])
def update_loja(loja_id):
    try:
        data = request.get_json()
        updated_loja = Loja_service.LujaService.update_loja(loja_id, data)
        if updated_loja:
            return jsonify(updated_loja.__dict__), 200
        else:
            return jsonify({'error': 'Loja não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@loja_bp.route('/lojas/<int:loja_id>', methods=['DELETE'])
def delete_loja(loja_id):
    try:
        deleted_loja = Loja_service.LujaService.delete_loja(loja_id)
        if deleted_loja:
            return jsonify({'message': 'Loja deletada com sucesso'}), 200
        else:
            return jsonify({'error': 'Loja não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400