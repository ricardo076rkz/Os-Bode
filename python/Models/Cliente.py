
from db import db
from Models.Usuario import Usuario

class Cliente(Usuario):
    __tablename__ = 'cliente'

    id = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id'),
        primary_key=True
    )

    telefone = db.Column(db.String(20), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'cliente'
    }

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'perfil': self.perfil,
            'telefone': self.telefone,
            'endereco': self.endereco
        }
