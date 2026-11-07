from Models import Cliente
from db import db

class ClienteRepository:


    @staticmethod
    def get_all_clientes(self):
        return Cliente.query.all()


    @staticmethod
    def get_by_id(self, cliente_id):
        return Cliente.query.get(cliente_id)


    @staticmethod
    def get_by_email(self, email):
        return Cliente.query.filter_by(email=email).first()
    
    @staticmethod
    def get_by_nome(self, nome):
        return Cliente.query.filter_by(nome=nome).first()


    @staticmethod
    def get_cliente_by_id(cliente_id):
        return Cliente.query.get(cliente_id)

    @staticmethod
    def create_cliente(nome, email, perfil, telefone, endereco):
        novo_cliente = Cliente(nome=nome, email=email, perfil=perfil, telefone=telefone, endereco=endereco)
        db.session.add(novo_cliente)
        db.session.commit()
        return novo_cliente

    @staticmethod
    def update_cliente(cliente_id, nome=None, email=None, perfil=None, telefone=None, endereco=None):
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            if nome:
                cliente.nome = nome
            if email:
                cliente.email = email
            if perfil:
                cliente.perfil = perfil
            if telefone:
                cliente.telefone = telefone
            if endereco:
                cliente.endereco = endereco
            db.session.commit()
        return cliente

    @staticmethod
    def delete_cliente(cliente_id):
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            db.session.delete(cliente)
            db.session.commit()
    