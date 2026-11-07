from Repository.UsuarioRepository import UsuarioRepository
from Models import Usuario
from Exception.Usuario_existente_exception import UsuarioExistenteException


class UsuarioService:
    
    @staticmethod
    def get_all_usuarios():
        return UsuarioRepository.get_all_usuarios()
        

    @staticmethod
    def get_usuario_by_id(Usuario_id):
        return UsuarioRepository.get_usuario_by_id(Usuario_id)

    @staticmethod
    def get_by_login(login):
        return UsuarioRepository.get_by_login(login)

    @staticmethod
    def create_usuario(Usuario):
        existing_Usuario = UsuarioRepository.get_by_email(Usuario.email)


        if existing_Usuario:
            raise UsuarioExistenteException("Usuário com este email já existe.")
        return UsuarioRepository.create_usuario(Usuario)

    @staticmethod
    def update_usuario(Usuario):
        return UsuarioRepository.update_usuario(Usuario)

    @staticmethod
    def delete_usuario(Usuario_id):
        return UsuarioRepository.delete_usuario(Usuario_id)

