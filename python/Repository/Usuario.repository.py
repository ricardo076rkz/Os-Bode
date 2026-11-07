from Models.Usuario import Usuario
from db import db

class UsuarioRepository:

    @staticmethod
    def get_all_usuarios():
        return Usuario.query.all()


    @staticmethod
    def get_usuario_by_id(usuario_id):
        return Usuario.query.get(usuario_id) 


    @staticmethod
    def get_by_login(login):
        return Usuario.query.filter_by(email=login).first()


    @staticmethod
    def create_usuario(usuario):
        try:
            existing_usuario = Usuario.query.filter_by(email=usuario.email).first()
            if existing_usuario:
                print("Erro: Usuário com este email já existe.")
                return None
            db.session.add(usuario)
            db.session.commit()
            return usuario
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar usuário: {e}")
            return None