from flask import Blueprint, jsonify, request
from Service import Lojista_service
from Models import Lojista


lojista_bp = Blueprint('lojista_bp', __name__)

@lojista_bp.route('/lojistas', methods=['GET'])
def get_all_lojistas():
    try:
        lojistas = Lojista_service.LojistaService.get_all_lojistas()
        return jsonify([lojista.__dict__ for lojista in lojistas]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@lojista_bp.route('/lojistas/<int:lojista_id>', methods=['GET'])
def get_lojista_by_id(lojista_id):
    try:
        lojista = Lojista_service.LojistaService.get_lojista_by_id(lojista_id)
        if lojista:
            return jsonify(lojista.__dict__), 200
        else:
            return jsonify({'error': 'Lojista não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@lojista_bp.route('/lojistas', methods=['POST'])
def create_lojista():
    try:
        data = request.get_json()
        new_lojista = Lojista(nome=data['nome'], email=data['email'], senha=data['senha'], perfil=data['perfil'])
        created_lojista = Lojista_service.LojistaService.create_lojista(new_lojista)
        if created_lojista:
            return jsonify(created_lojista.__dict__), 201
        else:
            return jsonify({'error': 'Erro ao criar lojista'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@lojista_bp.route('/lojistas/<int:lojista_id>', methods=['PUT'])
def update_lojista(lojista_id):
    try:
        data = request.get_json()
        updated_lojista = Lojista_service.LojistaService.update_lojista(lojista_id, data)
        if updated_lojista:
            return jsonify(updated_lojista.__dict__), 200
        else:
            return jsonify({'error': 'Lojista não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@lojista_bp.route('/lojistas/<int:lojista_id>', methods=['DELETE'])
def delete_lojista(lojista_id):
    try:
        deleted_lojista = Lojista_service.LojistaService.delete_lojista(lojista_id)
        if deleted_lojista:
            return jsonify({'message': 'Lojista deletado com sucesso'}), 200
        else:
            return jsonify({'error': 'Lojista não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@lojista_bp.route('/lojistas/email/<string:email>', methods=['GET'])
def get_lojista_by_email(email):
    try:
        lojista = Lojista_service.LojistaService.get_by_email(email)
        if lojista:
            return jsonify(lojista.__dict__), 200
        else:
            return jsonify({'error': 'Lojista não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400