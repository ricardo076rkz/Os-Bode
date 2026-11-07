class EmailExistenteException(Exception):
    def __init__(self, message="Email já existe."):
        self.message = message
        super().__init__(self.message)