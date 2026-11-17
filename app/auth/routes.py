from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Usuario
from app.forms import LoginForm
from app.forms import LoginForm, RegistroUsuarioForm
auth_bp = Blueprint('auth', __name__)
from app.models import db, Usuario, Rol
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.models import Rol, Usuario, db

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.activo:
            login_user(user)
            flash('Bienvenido/a, ' + user.username, 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/crear-usuario', methods=['GET', 'POST'])
@login_required
def crear_usuario():
    if current_user.rol.nombre != 'Gerente':
        flash('Solo el Gerente tiene acceso a esta sección', 'danger')
        return redirect(url_for('main.dashboard'))

    form = RegistroUsuarioForm()
    form.id_rol.choices = [(r.id_rol, r.nombre) for r in Rol.query.all()]

    if form.validate_on_submit():
        existe = Usuario.query.filter_by(username=form.username.data).first()
        if existe:
            flash('El nombre de usuario ya existe', 'danger')
        else:
            nuevo_usuario = Usuario(username=form.username.data, id_rol=form.id_rol.data)
            nuevo_usuario.set_password(form.password.data)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash(f'Empleado {nuevo_usuario.username} registrado con éxito', 'success')
            return redirect(url_for('main.dashboard'))

    return render_template('crear_usuario.html', form=form)




@auth_bp.route('/usuario/editar/<int:id_usuario>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id_usuario):
  if not current_user.es_gerente:
    flash('No tienes permisos para realizar esta acción.', 'danger')
    return redirect(url_for('main.dashboard'))

  usuario = Usuario.query.get_or_404(id_usuario)

  if request.method == 'POST':
    usuario.username = request.form.get('username')
    # Si agregaste selección de rol en el formulario:
    id_rol = request.form.get('id_rol')
    if id_rol:
      usuario.id_rol = id_rol

    db.session.commit()
    flash(f'Usuario {usuario.username} actualizado con éxito.', 'success')
    return redirect(url_for('main.dashboard'))

  roles = Rol.query.all()
  return render_template(
      'usuario_editar.html', usuario=usuario, roles=roles
  )


@auth_bp.route('/usuario/desactivar/<int:id_usuario>', methods=['POST', 'GET'])
@login_required
def desactivar_usuario(id_usuario):
  if not current_user.es_gerente:
    flash('No tienes permisos para realizar esta acción.', 'danger')
    return redirect(url_for('main.dashboard'))

  usuario = Usuario.query.get_or_404(id_usuario)

  # Evitamos que el administrador se desactive a sí mismo por error
  if usuario.id_usuario == current_user.id_usuario:
    flash('No puedes desactivar tu propia cuenta activa.', 'danger')
    return redirect(url_for('main.dashboard'))

  # Si tu tabla tiene una columna 'activo', la alternamos o pasamos a False
  # (Si manejas borrado físico, puedes usar db.session.delete(usuario))
  usuario.activo = False
  db.session.commit()

  flash(
      f'El usuario {usuario.username} ha sido desactivado del sistema.',
      'warning',
  )
  return redirect(url_for('main.dashboard'))
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('auth.login'))
