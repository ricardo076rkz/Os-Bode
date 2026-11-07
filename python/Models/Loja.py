from Models import Lojista

class Loja(Lojista):

    __tablename__ = 'loja'
    id = db.Column(db.Integer, db.ForeignKey('lojista.id'), primary_key=True)
    nome_loja = db.Column(db.String(100), nullable=False)
    lojista_id = db.Column(db.Integer, db.ForeignKey('lojista.id'), nullable=False)
    segmento = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    avaliacao_media = db.Column(db.Float, nullable=False)
    
    localizacao = db.relationship('Localizacao', backref='loja', uselist=False, cascade="all, delete-orphan")


    def to_dict(self):
        return {
            'id': self.id,
            'nome_loja': self.nome_loja,
            'lojista_id': self.lojista_id,
            'segmento': self.segmento,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'avaliacao_media': self.avaliacao_media
            
        }