class Evento(db.Model):


   
   __tablename__ = 'evento'
   id = db.Column(db.Integer, primary_key=True)
   nome_evento = db.Column(db.String(100), nullable=False)
   dia_semana = db.Column(db.String(20), nullable=False)
   horario = db.Column(db.String(20), nullable=False)
   descricao = db.Column(db.String(200), nullable=False)
   latitude = db.Column(db.Float, nullable=False)
   longitude = db.Column(db.Float, nullable=False)




   def to_dict(self):
       return {
           'id': self.id,
           'nome_evento': self.nome_evento,
           'dia_semana': self.dia_semana,
           'horario': self.horario,
           'descricao': self.descricao,
           'latitude': self.latitude,
           'longitude': self.longitude
       }