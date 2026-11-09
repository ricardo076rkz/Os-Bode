from flask import Blueprint, jsonify, request
from Models import Avaliacao
from Service import Avaliacao_service


@avaliacao_bp.route('/avaliacoes', methods=['GET'])
def get_all_avaliacoes():
    try:
        avaliacoes = Avaliacao_service.AvaliacaoService.get_all_avaliacoes()
        return jsonify([avaliacao.__dict__ for avaliacao in avaliacoes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400



@avaliacao_bp.route('/avaliacoes/<int:avaliacao_id>', methods=['GET'])
def get_avaliacao_by_id(avaliacao_id):
    try:
        avaliacao = Avaliacao_service.AvaliacaoService.get_avaliacao_by_id(avaliacao_id)
        if avaliacao:
            return jsonify(avaliacao.__dict__), 200
        else:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@avaliacao_bp.route('/avaliacoes', methods=['POST'])
def create_avaliacao():
    try:
        data = request.get_json()
        new_avaliacao = Avaliacao(nota=data['nota'], comentario=data['comentario'], cliente_id=data['cliente_id'], lojista_id=data['lojista_id'])
        created_avaliacao = Avaliacao_service.AvaliacaoService.create_avaliacao(new_avaliacao)
        if created_avaliacao:
            return jsonify(created_avaliacao.__dict__), 201
        else:
            return jsonify({'error': 'Erro ao criar avaliação'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@avaliacao_bp.route('/avaliacoes/<int:avaliacao_id>', methods=['PUT'])
def update_avaliacao(avaliacao_id):
    try:
        data = request.get_json()
        updated_avaliacao = Avaliacao_service.AvaliacaoService.update_avaliacao(avaliacao_id, data)
        if updated_avaliacao:
            return jsonify(updated_avaliacao.__dict__), 200
        else:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@avaliacao_bp.route('/avaliacoes/<int:avaliacao_id>', methods=['DELETE'])
def delete_avaliacao(avaliacao_id):
    try:
        deleted_avaliacao = Avaliacao_service.AvaliacaoService.delete_avaliacao(avaliacao_id)
        if deleted_avaliacao:
            return jsonify({'message': 'Avaliação deletada com sucesso'}), 200
        else:
            return jsonify({'error': 'Avaliação não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@avaliacao_bp.route('/avaliacoes/cliente/<int:cliente_id>', methods=['GET'])
def get_avaliacoes_by_cliente(cliente_id):
    try:
        avaliacoes = Avaliacao_service.AvaliacaoService.get_avaliacoes_by_cliente(cliente_id)
        if avaliacoes:
            return jsonify([avaliacao.__dict__ for avaliacao in avaliacoes]), 200
        else:
            return jsonify({'error': 'Nenhuma avaliação encontrada para este cliente'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400