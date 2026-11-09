from Models import Loja


class Localizacao(db.Model):
    __tablename__ = 'localizacoes_lojas'
    
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    loja_id = db.Column(db.Integer, db.ForeignKey('lojas.id'), unique=True, nullable=False)
    bairro = db.Column(db.String(50))
    cidade = db.Column(db.String(50))