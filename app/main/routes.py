from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.models import Alerta, Cita, Cliente, Rol, Usuario, db
from app.forms import ClienteForm

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    alertas = []
    citas_del_dia = []
    lista_usuarios = []

    if current_user.es_gerente:
        alertas = (
            Alerta.query.filter_by(leida=False)
            .order_by(Alerta.fecha.desc())
            .limit(10)
            .all()
        )
        lista_usuarios = Usuario.query.all()
    elif current_user.es_recepcionista:
        citas_del_dia = Cita.query.order_by(Cita.fecha_hora.asc()).all()
    elif current_user.rol.nombre in ['Asistente', 'Asistente de estilista', 'Estilista']:
        # El asistente, asistente de estilista o estilista solo ve las citas donde está participando
        citas_del_dia = (
            Cita.query.filter(
                (Cita.id_estilista == current_user.id_usuario)
                | (Cita.id_asistente == current_user.id_usuario)
            )
            .order_by(Cita.fecha_hora.asc())
            .all()
        )

    return render_template(
        'dashboard.html',
        alertas=alertas,
        citas_del_dia=citas_del_dia,
        lista_usuarios=lista_usuarios,
    )


@main_bp.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if not current_user.es_recepcionista and not current_user.es_gerente:
        flash('No tienes permisos para registrar clientes.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            nombre=form.nombre.data,
            telefono=form.telefono.data,
            email=form.email.data,
            notas_generales=form.notas_generales.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f'Cliente {cliente.nombre} registrado con éxito.', 'success')
        return redirect(url_for('main.nueva_cita'))

    return render_template('cliente_form.html', form=form, titulo='Registrar Nuevo Cliente')


@main_bp.route('/citas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_cita():
    if not current_user.es_recepcionista:
        flash('Solo la recepcionista puede gestionar la creación de citas.', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        id_cliente = request.form.get('id_cliente')
        id_estilista = request.form.get('id_estilista')
        id_asistente = request.form.get('id_asistente')
        fecha_hora_str = request.form.get('fecha_hora')

        fecha_hora = datetime.strptime(fecha_hora_str, '%Y-%m-%dT%H:%M')

        nueva = Cita(
            id_cliente=id_cliente,
            id_estilista=id_estilista,
            id_asistente=id_asistente if id_asistente else None,
            fecha_hora=fecha_hora,
            estado='PROGRAMADA'
        )
        db.session.add(nueva)
        db.session.commit()

        flash('Cita agendada con éxito en el sistema.', 'success')
        return redirect(url_for('main.dashboard'))

    # Si es método GET, cargamos las listas para los selectores del formulario
    clientes = Cliente.query.all()
    estilistas = Usuario.query.join(Usuario.rol).filter(Rol.nombre == 'Estilista').all()
    asistentes = Usuario.query.join(Usuario.rol).filter(Rol.nombre.in_(['Asistente', 'Asistente de estilista'])).all()

    return render_template(
        'cita_form.html',
        clientes=clientes,
        estilistas=estilistas,
        asistentes=asistentes
    )