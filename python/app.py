from init_db import init_db
from flask import Flask, Blueprint, request, json
from Config import Config
from db import db
from Controller.Cliente_controller import cliente_bp
from Controller.Auth_controller import auth_bp
from Controller.Evento_controller import evento_bp
from Controller.Lojista_controller import lojista_bp
from Controller.Usuario_controller import usuario_bp
from Controller.Avaliacao_controller import avaliacao_bp
from Controller.Loja_controller import loja_bp

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

init_db(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(lojista_bp, url_prefix='/api/lojistas')
app.register_blueprint(cliente_bp, url_prefix='/api/clientes')
app.register_blueprint(loja_bp, url_prefix='/api/lojas')
app.register_blueprint(evento_bp, url_prefix='/api/eventos')
app.register_blueprint(avaliacao_bp, url_prefix='/api/avaliacoes')
app.register_blueprint(usuario_bp, url_prefix='/api/usuarios')


if __name__ == '__main__':
    app.run(debug=True)
