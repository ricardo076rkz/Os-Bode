from Models import Evento
from Repository.Evento_repository import EventoRepository


class EventoService:

    @staticmethod
    def get_all_eventos():
        return EventoRepository.get_all_eventos()

    @staticmethod
    def get_evento_by_id(evento_id):
        return EventoRepository.get_evento_by_id(evento_id)

    @staticmethod
    def create_evento(nome_evento, dia_semana, horario, descricao, latitude, longitude):
        return EventoRepository.create_evento(nome_evento, dia_semana, horario, descricao, latitude, longitude)

    @staticmethod
    def update_evento(evento_id, nome_evento=None, dia_semana=None, horario=None, descricao=None, latitude=None, longitude=None):
        return EventoRepository.update_evento(evento_id, nome_evento, dia_semana, horario, descricao, latitude, longitude)

    @staticmethod
    def delete_evento(evento_id):
        return EventoRepository.delete_evento(evento_id)