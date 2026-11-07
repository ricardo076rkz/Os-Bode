from Models import Avaliacao
from db import db


class AvaliacaoRepository:

    @staticmethod
    def get_all_avaliacoes():
        return Avaliacao.query.all()

    @staticmethod
    def get_avaliacao_by_id(avaliacao_id):
        return Avaliacao.query.get(avaliacao_id)

    @staticmethod
    def create_avaliacao(nota, comentario, loja_id):
        new_avaliacao = Avaliacao(
            nota=nota,
            comentario=comentario,
            loja_id=loja_id
        )
        db.session.add(new_avaliacao)
        db.session.commit()
        return new_avaliacao
