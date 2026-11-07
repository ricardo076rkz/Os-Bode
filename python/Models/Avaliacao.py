from db import db

class avaliacao(db.Model):
    __tablename__ = 'avaliacao'
    id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    nota = db.Column(db.Float, nullable=False)
    comentario = db.Column(db.String(200), nullable=True)
    loja_id = db.Column(db.Integer, db.ForeignKey('loja.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    data_criação = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    cliente = db.relationship('Cliente', backref=db.backref('avaliacoes', lazy=True))
    lojista = db.relationship('Loja', backref=db.backref('avaliacoes', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'nota': self.nota,
            'comentario': self.comentario,
            'loja_id': self.loja_id,
            'cliente_id': self.cliente_id,
            'data_criação': self.data_criação
        }
 