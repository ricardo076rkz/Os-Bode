class UsuarioExistenteException(Exception):
    def __init__(self, message="Usuário já existe."):
        self.message = message
        super().__init__(self.message)