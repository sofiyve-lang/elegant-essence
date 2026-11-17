from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, Producto, Movimiento, Alerta
from app.forms import ProductoForm
from functools import wraps
from flask import jsonify, request
from app.forms import ConsumoForm, ProductoForm, RestockForm

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventario')

def rol_requerido(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.rol.nombre not in roles:
                flash('No tienes permiso para esta acción', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

@inventory_bp.route('/')
@login_required
def lista_productos():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    return render_template('inventario.html', productos=productos)

@inventory_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@rol_requerido('Gerente')  # <-- Restringido exclusivamente al Gerente según RF-06
def nuevo_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        existe = Producto.query.filter_by(codigo_barras=form.codigo_barras.data).first()
        if existe:
            flash('Ese código de barras ya existe', 'danger')
        else:
            p = Producto(
                codigo_barras=form.codigo_barras.data,
                nombre=form.nombre.data,
                ml_por_envase=form.ml_por_envase.data,
                stock_minimo_ml=form.stock_minimo_ml.data,
                stock_total_ml=0
            )
            db.session.add(p)
            db.session.commit()
            flash('Producto creado correctamente', 'success')
            return redirect(url_for('inventory.lista_productos'))
    return render_template('producto_form.html', form=form, titulo='Nuevo producto')


@inventory_bp.route('/api/buscar', methods=['GET'])
@login_required
def api_buscar_producto():
    # Obtenemos el código de barras que manda el JavaScript de la vista
    codigo = request.args.get('codigo', '').strip()

    if not codigo:
        return jsonify({'encontrado': False, 'mensaje': 'Código no proporcionado'})

    # Buscamos el producto en la base de datos por su código de barras
    producto = Producto.query.filter_by(codigo_barras=codigo, activo=True).first()

    if producto:
        # Si existe, regresamos sus datos empaquetados en JSON
        return jsonify({
            'encontrado': True,
            'id_producto': producto.id_producto,
            'nombre': producto.nombre,
            'ml_por_envase': producto.ml_por_envase,
            'stock_total_ml': producto.stock_total_ml,
            'envases_enteros': producto.envases_enteros,
            'ml_sobrantes': producto.ml_sobrantes,
            'stock_minimo_ml': producto.stock_minimo_ml
        })
    else:
        # Si no existe, avisamos para que el frontend decida si redirige al alta
        return jsonify({
            'encontrado': False,
            'mensaje': 'Producto no registrado en el sistema'
        })

@inventory_bp.route('/consumo', methods=['GET', 'POST'])
@login_required
@rol_requerido('Gerente', 'Estilista', 'Asistente')
def registrar_consumo():
    if request.method == 'POST':
        # Obtenemos los datos enviados desde el formulario HTML
        id_producto = request.form.get('id_producto')
        codigo_barras = request.form.get('codigo_barras')
        ml_str = request.form.get('mililitros') or request.form.get('ml_usados')

        if not ml_str:
            flash('Por favor ingresa la cantidad de mililitros utilizados.', 'danger')
            return redirect(url_for('inventory.registrar_consumo'))

        try:
            ml_gastados = float(ml_str)
        except ValueError:
            flash('Cantidad de mililitros inválida.', 'danger')
            return redirect(url_for('inventory.registrar_consumo'))

        # Buscamos el producto ya sea por ID (menú desplegable) o por código de barras
        if id_producto:
            producto = Producto.query.get(id_producto)
        elif codigo_barras:
            producto = Producto.query.filter_by(codigo_barras=codigo_barras, activo=True).first()
        else:
            flash('Debes seleccionar un producto del inventario.', 'danger')
            return redirect(url_for('inventory.registrar_consumo'))

        if not producto or not producto.activo:
            flash('El producto seleccionado no existe o está inactivo.', 'danger')
            return redirect(url_for('inventory.registrar_consumo'))

        # Validación de seguridad: stock suficiente
        if ml_gastados > producto.stock_total_ml:
            flash(f'Stock insuficiente. Disponibles: {producto.stock_total_ml} ml', 'danger')
            return redirect(url_for('inventory.registrar_consumo'))

        # Descuento atómico del inventario en mililitros
        producto.stock_total_ml -= ml_gastados

        # Registro del movimiento en la bitácora (Trazabilidad)
        movimiento = Movimiento(
            id_producto=producto.id_producto,
            id_usuario=current_user.id_usuario,
            tipo='USO',
            cantidad_ml=ml_gastados,
            justificacion='Consumo aplicado en servicio (Punto de Uso)'
        )
        db.session.add(movimiento)

        # Verificación de stock mínimo para generar Alerta automática si aplica
        if producto.stock_total_ml <= producto.stock_minimo_ml:
            alerta = Alerta(
                id_producto=producto.id_producto,
                stock_actual_ml=producto.stock_total_ml,
                leida=False
            )
            db.session.add(alerta)

        db.session.commit()
        flash(f'Se descontaron {ml_gastados} ml de {producto.nombre} exitosamente.', 'success')
        return redirect(url_for('inventory.registrar_consumo'))

    # Si es método GET, cargamos los productos activos para que se desplieguen en el selector
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    return render_template('consumo_form.html', productos=productos, titulo='Punto de Uso - Descuento de Producto')


@inventory_bp.route('/restock', methods=['GET', 'POST'])
@login_required
@rol_requerido('Gerente', 'Recepcionista')  # Restringido según diseño funcional
def registrar_restock():
    form = RestockForm()

    if form.validate_on_submit():
        # 1. Buscamos el producto por el código de barras escaneado
        producto = Producto.query.filter_by(codigo_barras=form.codigo_barras.data, activo=True).first()

        if not producto:
            flash('El producto no se encuentra registrado en el sistema', 'danger')
            return redirect(url_for('inventory.registrar_restock'))

        # 2. Lógica de cálculo (RF-07): Envases * ml_por_envase
        envases = form.envases_recibidos.data
        ml_agregados = envases * producto.ml_por_envase

        # 3. Sumar al stock total en mililitros de forma atómica
        producto.stock_total_ml += ml_agregados

        # 4. Registrar el movimiento en la bitácora de trazabilidad
        movimiento = Movimiento(
            id_producto=producto.id_producto,
            id_usuario=current_user.id_usuario,
            tipo='RESTOCK',
            cantidad_ml=ml_agregados,
            justificacion=f'Recepción de proveedor: {envases} envases ({ml_agregados} ml)'
        )
        db.session.add(movimiento)

        # 5. Guardar cambios en la base de datos (Neon PostgreSQL)
        db.session.commit()

        flash(f'Restock exitoso: Se sumaron {ml_agregados} ml ({envases} envases) a {producto.nombre}', 'success')
        return redirect(url_for('inventory.lista_productos'))

    return render_template('restock_form.html', form=form, titulo='Recepción de Mercancía - Restock')