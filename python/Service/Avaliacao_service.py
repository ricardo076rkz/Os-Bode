from Models import Avaliacao
from Repository.Avaliacao_repository import AvaliacaoRepository


class AvaliacaoService:
    @staticmethod
    def get_all_avaliacoes():
        return AvaliacaoRepository.get_all_avaliacoes()

    @staticmethod
    def get_avaliacao_by_id(avaliacao_id):
        return AvaliacaoRepository.get_avaliacao_by_id(avaliacao_id)

    @staticmethod
    def create_avaliacao(nota, comentario, loja_id):
        return AvaliacaoRepository.create_avaliacao(nota, comentario, loja_id)