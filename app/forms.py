from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Optional

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar sesión')


class ProductoForm(FlaskForm):
    codigo_barras = StringField('Código de barras', validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[DataRequired()])
    ml_por_envase = IntegerField('ml por envase', validators=[DataRequired(), NumberRange(min=1)])
    stock_minimo_ml = IntegerField('Stock mínimo (ml)', validators=[DataRequired(), NumberRange(min=0)])
    precio = StringField('Precio', validators=[Optional()])
    submit = SubmitField('Guardar')


class ConsumoForm(FlaskForm):
    codigo_barras = StringField('Código de barras', validators=[DataRequired()])
    # Añadido el max=300 para cumplir estrictamente con RF-10
    ml_usados = IntegerField('Mililitros usados', validators=[DataRequired(), NumberRange(min=1, max=300)])
    id_cliente = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    notas = TextAreaField('Notas de la fórmula', validators=[Optional()])
    submit = SubmitField('Registrar consumo')
class RegistroUsuarioForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    id_rol = SelectField('Rol del Empleado', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Registrar Empleado')

class RestockForm(FlaskForm):
    codigo_barras = StringField('Código de barras', validators=[DataRequired()])
    envases_recibidos = IntegerField('Envases recibidos', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Registrar Entrada de Mercancía')

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[Optional()])
    email = StringField('Correo electrónico', validators=[Optional(), Email()])
    notas_generales = TextAreaField('Notas / Preferencias', validators=[Optional()])
    submit = SubmitField('Guardar Cliente')