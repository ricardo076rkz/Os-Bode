from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash
from Models import Usuario
from Service import Usuario_service
from Exception import Usuario_existente_exception


usuario_bp = Blueprint('usuario_bp', __name__)

@usuario_bp.route('/usuarios', methods=['GET'])
def get_all_usuarios():
    try:
        usuarios = UsuarioService.get_all_usuarios()
        return jsonify([usuario.__dict__ for usuario in usuarios]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@usuario_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
def get_usuario_by_id(usuario_id):
    try:
        usuario = UsuarioService.get_usuario_by_id(usuario_id)
        if usuario:
            return jsonify(usuario.__dict__), 200
        else:
            return jsonify({'error': 'Usuário não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@usuario_bp.route('/usuarios/login/<string:login>', methods=['GET'])
def get_usuario_by_login(login):
    try:
        usuario = UsuarioService.get_by_login(login)
        if usuario:
            return jsonify(usuario.__dict__), 200
        else:
            return jsonify({'error': 'Usuário não encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@usuario_bp.route('/usuarios', methods=['POST'])
def create_usuario():
    try:
        data = request.get_json()
        hashed_password = generate_password_hash(data['senha'], method='sha256')
        new_usuario = Usuario(nome=data['nome'], email=data['email'], senha=hashed_password, perfil=data['perfil'])
        created_usuario = UsuarioService.create_usuario(new_usuario)
        if created_usuario:
            return jsonify(created_usuario.__dict__), 201
        else:
            return jsonify({'error': 'Erro ao criar usuário'}), 400
    except Usuario_existente_exception.UsuarioExistenteException as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400




@usuario_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
def update_usuario(usuario_id):
    try:
        data = request.get_json()
        usuario_to_update = Usuario(id=usuario_id, nome=data['nome'], email=data['email'], senha=data['senha'], perfil=data['perfil'])
        updated_usuario = UsuarioService.update_usuario(usuario_to_update)
        if updated_usuario:
            return jsonify(updated_usuario.__dict__), 200
        else:
            return jsonify({'error': 'Erro ao atualizar usuário'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@usuario_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
def delete_usuario(usuario_id):
    try:
        result = UsuarioService.delete_usuario(usuario_id)
        if result:
            return jsonify({'message': 'Usuário deletado com sucesso'}), 200
        else:
            return jsonify({'error': 'Erro ao deletar usuário'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400
