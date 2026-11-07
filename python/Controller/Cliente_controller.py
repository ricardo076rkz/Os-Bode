from flask import Blueprint, jsonify, request
from Service import Cliente_service
from Models import Cliente
from Exception import Email_existente


cliente_bp = Blueprint('cliente_bp', __name__)

@cliente_bp.route('/clientes', methods=['GET'])
def get_all_clientes():
    try:
        clientes = Cliente_service.ClienteService.get_all_clientes()
        return jsonify([cliente.__dict__ for cliente in clientes]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
def get_cliente_by_id(cliente_id):
    try:
        cliente = Cliente_service.ClienteService.get_cliente_by_id(cliente_id)
        if cliente:
            return jsonify(cliente.__dict__), 200
        else:
            return jsonify({'error': 'Cliente não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    
@cliente_bp.route('/clientes/email/<string:email>', methods=['GET'])
def get_cliente_by_email(email):
    try:
        cliente = Cliente_service.ClienteService.get_by_email(email)
        if cliente:
            return jsonify(cliente.__dict__), 200
        else:
            return jsonify({'error': 'Cliente não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@cliente_bp.route('/clientes', methods=['POST'])
def create_cliente():
    try:
        data = request.get_json()
        new_cliente = Cliente(nome=data['nome'], email=data['email'], perfil=data['perfil'], telefone=data['telefone'], endereco=data['endereco'])
        created_cliente = Cliente_service.ClienteService.create_cliente(new_cliente.nome, new_cliente.email, new_cliente.perfil, new_cliente.telefone, new_cliente.endereco)
        if created_cliente:
            return jsonify(created_cliente.__dict__), 201
        else:
            return jsonify({'error': 'Erro ao criar cliente'}), 400
    except Email_existente.EmailExistenteException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@cliente_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
def update_cliente(cliente_id):
    try:
        data = request.get_json()
        updated_cliente = Cliente_service.ClienteService.update_cliente(
            cliente_id,
            nome=data.get('nome'),
            email=data.get('email'),
            perfil=data.get('perfil'),
            telefone=data.get('telefone'),
            endereco=data.get('endereco')
        )
        if updated_cliente:
            return jsonify(updated_cliente.__dict__), 200
        else:
            return jsonify({'error': 'Erro ao atualizar cliente'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    

@cliente_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
def delete_cliente(cliente_id):
    try:
        result = Cliente_service.ClienteService.delete_cliente(cliente_id)
        if result:
            return jsonify({'message': 'Cliente deletado com sucesso'}), 200
        else:
            return jsonify({'error': 'Erro ao deletar cliente'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@cliente_bp.route('/clientes/nome/<string:nome>', methods=['GET'])
def get_cliente_by_nome(nome):
    try:
        cliente = Cliente_service.ClienteService.get_by_nome(nome)
        if cliente:
            return jsonify(cliente.__dict__), 200
        else:
            return jsonify({'error': 'Cliente não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400