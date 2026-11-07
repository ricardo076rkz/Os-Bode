class UsuarioLoginExistenteException(Exception):
    def __init__(self, message="Login de usuário já existe."):
        self.message = message
        super().__init__(self.message)