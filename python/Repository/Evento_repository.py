from Models.Evento import Evento
from db import db


class EventoRepository:

    @staticmethod
    def get_all_eventos():
        return Evento.query.all()

    @staticmethod
    def get_evento_by_id(evento_id):
        return Evento.query.get(evento_id)

    @staticmethod
    def create_evento(nome_evento, descricao, data_inicio, data_fim, loja_id):
        new_evento = Evento(
            nome_evento=nome_evento,
            descricao=descricao,
            data_inicio=data_inicio,
            data_fim=data_fim,
            loja_id=loja_id
        )
        db.session.add(new_evento)
        db.session.commit()
        return new_evento

    @staticmethod
    def update_evento(evento_id, nome_evento=None, descricao=None, data_inicio=None, data_fim=None):
        evento = Evento.query.get(evento_id)
        if evento:
            if nome_evento is not None:
                evento.nome_evento = nome_evento
            if descricao is not None:
                evento.descricao = descricao
            if data_inicio is not None:
                evento.data_inicio = data_inicio
            if data_fim is not None:
                evento.data_fim = data_fim
            db.session.commit()
        return evento

    @staticmethod
    def delete_evento(evento_id):
        evento = Evento.query.get(evento_id)
        if evento:
            db.session.delete(evento)
            db.session.commit()
        return evento


