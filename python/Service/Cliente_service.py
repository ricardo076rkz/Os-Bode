from Models import Cliente
from Repository.Cliente_repository import ClienteRepository
from exception.Usuario_existente_exception import UsuarioExistenteException
from exception.Usuario_login_existente import UsuarioLoginExistenteException



class ClienteService:
    @staticmethod
    def get_all_clientes():
        return ClienteRepository.get_all_clientes()


    @staticmethod
    def get_cliente_by_id(Cliente_id):
        return ClienteRepository.get_cliente_by_id(Cliente_id)


    @staticmethod
    def get_by_email(email):
        return ClienteRepository.get_by_email(email)


    @staticmethod
    def create_cliente(nome, email, perfil, telefone, endereco):
        existing_cliente = ClienteRepository.get_by_email(email)
        if existing_cliente:
            raise UsuarioExistenteException("Cliente com este email já existe.")
        
        existing_cliente_nome = ClienteRepository.get_by_nome(nome)
        if existing_cliente_nome:
            raise UsuarioLoginExistenteException("Cliente com este nome já existe.")

        return ClienteRepository.create_cliente(nome, email, perfil, telefone, endereco)


    @staticmethod
    def update_cliente(Cliente_id, nome=None, email=None, perfil=None, telefone=None, endereco=None):
        return ClienteRepository.update_cliente(Cliente_id, nome, email, perfil, telefone, endereco)


    @staticmethod
    def delete_cliente(Cliente_id):
        return ClienteRepository.delete_cliente(Cliente_id)