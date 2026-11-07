from Models import Loja
from Repository.Loja_repository import LojaRepository

class LojaService:
    @staticmethod
    def get_all_lojas():
        return LojaRepository.get_all_lojas()

    @staticmethod
    def get_loja_by_id(loja_id):
        return LojaRepository.get_loja_by_id(loja_id)

    @staticmethod
    def create_loja(nome_loja, lojista_id, segmento, latitude, longitude, avaliacao_media):
        return LojaRepository.create_loja(nome_loja, lojista_id, segmento, latitude, longitude, avaliacao_media)

    @staticmethod
    def update_loja(loja_id, nome_loja=None, segmento=None, latitude=None, longitude=None, avaliacao_media=None):
        return LojaRepository.update_loja(loja_id, nome_loja, segmento, latitude, longitude, avaliacao_media)

    @staticmethod
    def delete_loja(loja_id):
        return LojaRepository.delete_loja(loja_id)