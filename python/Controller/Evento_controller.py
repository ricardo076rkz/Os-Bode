from flask import Blueprint, jsonify, request
from Models import Evento
from Service import Evento_service

evento_bp = Blueprint('evento_bp', __name__)

@evento_bp.route('/eventos', methods=['GET'])
def get_all_eventos():
    try:
        eventos = Evento_service.EventoService.get_all_eventos()
        return jsonify([evento.__dict__ for evento in eventos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@evento_bp.route('/eventos/<int:evento_id>', methods=['GET'])
def get_evento_by_id(evento_id):
    try:
        evento = Evento_service.EventoService.get_evento_by_id(evento_id)
        if evento:
            return jsonify(evento.__dict__), 200
        else:
            return jsonify({'error': 'Evento não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@evento_bp.route('/eventos', methods=['POST'])
def create_evento():
    try:
        data = request.get_json()
        new_evento = Evento(nome=data['nome'], descricao=data['descricao'], data=data['data'], local=data['local'])
        created_evento = Evento_service.EventoService.create_evento(new_evento)
        if created_evento:
            return jsonify(created_evento.__dict__), 201
        else:
            return jsonify({'error': 'Erro ao criar evento'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@evento_bp.route('/eventos/<int:evento_id>', methods=['PUT'])
def update_evento(evento_id):
    try:
        data = request.get_json()
        updated_evento = Evento_service.EventoService.update_evento(evento_id, data)
        if updated_evento:
            return jsonify(updated_evento.__dict__), 200
        else:
            return jsonify({'error': 'Evento não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@evento_bp.route('/eventos/<int:evento_id>', methods=['DELETE'])
def delete_evento(evento_id):
    try:
        deleted_evento = Evento_service.EventoService.delete_evento(evento_id)
        if deleted_evento:
            return jsonify({'message': 'Evento deletado com sucesso'}), 200
        else:
            return jsonify({'error': 'Evento não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400