from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Rol(db.Model):
  __tablename__ = 'roles'

  id_rol = db.Column(db.Integer, primary_key=True)
  nombre = db.Column(db.String(50), unique=True, nullable=False)

  # La relación hacia usuarios usa backref='rol_obj' o simplemente se define sin colisionar
  # (o puedes omitir el backref en Rol y dejarlo solo en Usuario)


class Usuario(db.Model, UserMixin):
  __tablename__ = 'usuarios'

  id_usuario = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password_hash = db.Column(db.String(255), nullable=False)
  id_rol = db.Column(
      db.Integer, db.ForeignKey('roles.id_rol'), nullable=False
  )
  activo = db.Column(db.Boolean, default=True, nullable=False)

  rol = db.relationship('Rol', backref=db.backref('lista_usuarios', lazy=True))

  # Aquí definimos la relación con un backref único que no se llame 'rol'
  rol = db.relationship('Rol', backref=db.backref('lista_usuarios', lazy=True))

  def get_id(self):
      return str(self.id_usuario)

  def check_password(self, password):
      return check_password_hash(self.password_hash, password)
  # Propiedades helper para verificar roles
  @property
  def es_gerente(self):
    return self.rol and self.rol.nombre.lower() in [
        'gerente',
        'administrador',
        'admin',
    ]

  @property
  def es_recepcionista(self):
    return self.rol and self.rol.nombre.lower() in [
        'recepcionista',
        'recepcion',
    ]

  @property
  def es_estilista(self):
    return self.rol and self.rol.nombre.lower() in [
        'estilista',
        'asistente',
        'asistente de estilista',
    ]

  def set_password(self, password):
      self.password_hash = generate_password_hash(password)

  def check_password(self, password):
      return check_password_hash(self.password_hash, password)

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(30))
    email = db.Column(db.String(120))
    notas_generales = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    formulas = db.relationship('Formula', backref='cliente', lazy=True)


class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    ml_por_envase = db.Column(db.Integer, nullable=False)
    stock_total_ml = db.Column(db.Integer, default=0)
    stock_minimo_ml = db.Column(db.Integer, default=0)
    precio = db.Column(db.Numeric(10, 2), default=0)
    activo = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.CheckConstraint('stock_total_ml >= 0', name='check_stock_positivo'),
        db.CheckConstraint('ml_por_envase > 0', name='check_ml_envase_positivo'),
    )

    @property
    def envases_enteros(self):
        return self.stock_total_ml // self.ml_por_envase

    @property
    def ml_sobrantes(self):
        return self.stock_total_ml % self.ml_por_envase


class Formula(db.Model):
    __tablename__ = 'formulas'
    id_formula = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False)
    id_usuario_estilista = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    notas_completas = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    detalles = db.relationship('DetalleFormula', backref='formula', lazy=True, cascade='all, delete-orphan')


class DetalleFormula(db.Model):
    __tablename__ = 'detalle_formula'
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_formula = db.Column(db.Integer, db.ForeignKey('formulas.id_formula'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    ml_usados = db.Column(db.Integer, nullable=False)
    producto = db.relationship('Producto')


class Movimiento(db.Model):
    __tablename__ = 'movimientos'
    id_movimiento = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # RESTOCK, USO, MERMA
    cantidad_ml = db.Column(db.Integer, nullable=False)
    id_formula = db.Column(db.Integer, db.ForeignKey('formulas.id_formula'))
    justificacion = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    producto = db.relationship('Producto')
    usuario = db.relationship('Usuario')


class Alerta(db.Model):
    __tablename__ = 'alertas'
    id_alerta = db.Column(db.Integer, primary_key=True)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)
    stock_actual_ml = db.Column(db.Integer)
    leida = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    producto = db.relationship('Producto')

class Cita(db.Model):
  __tablename__ = 'citas'  # <-- Esto fuerza a SQLAlchemy a buscar la tabla 'citas' exactamente

  id_cita = db.Column(db.Integer, primary_key=True)
  id_cliente = db.Column(
      db.Integer, db.ForeignKey('clientes.id_cliente'), nullable=False
  )
  id_estilista = db.Column(
      db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False
  )
  id_asistente = db.Column(
      db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True
  )
  fecha_hora = db.Column(db.DateTime, nullable=False)
  estado = db.Column(db.String(20), default='PROGRAMADA')
  created_at = db.Column(db.DateTime, default=datetime.utcnow)

  cliente = db.relationship('Cliente', backref='citas')
  estilista = db.relationship(
      'Usuario', foreign_keys=[id_estilista], backref='citas_asignadas'
  )