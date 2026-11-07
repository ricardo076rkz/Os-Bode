from Models.Loja import Loja
from db import db

class LojaRepository:
    
    @staticmethod
    def get_all_lojas():
        return Loja.query.all()

    @staticmethod
    def get_loja_by_id(loja_id):
        return Loja.query.get(loja_id)

    @staticmethod
    def create_loja(nome_loja, lojista_id, segmento, latitude, longitude, avaliacao_media):
        new_loja = Loja(
            nome_loja=nome_loja,
            lojista_id=lojista_id,
            segmento=segmento,
            latitude=latitude,
            longitude=longitude,
            avaliacao_media=avaliacao_media
        )
        db.session.add(new_loja)
        db.session.commit()
        return new_loja

    @staticmethod
    def update_loja(loja_id, nome_loja=None, segmento=None, latitude=None, longitude=None, avaliacao_media=None):
        loja = Loja.query.get(loja_id)
        if loja:
            if nome_loja is not None:
                loja.nome_loja = nome_loja
            if segmento is not None:
                loja.segmento = segmento
            if latitude is not None:
                loja.latitude = latitude
            if longitude is not None:
                loja.longitude = longitude
            if avaliacao_media is not None:
                loja.avaliacao_media = avaliacao_media
            db.session.commit()
        return loja

    @staticmethod
    def delete_loja(loja_id):
        loja = Loja.query.get(loja_id)
        if loja:
            db.session.delete(loja)
            db.session.commit()
        return loja