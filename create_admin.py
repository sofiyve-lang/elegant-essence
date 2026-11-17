from app import create_app
from app.models import db, Usuario, Rol

app = create_app()

with app.app_context():
    # Buscar el rol Gerente
    rol_gerente = Rol.query.filter_by(nombre='Gerente').first()
    if not rol_gerente:
        print('Error: no existe el rol Gerente. Ejecuta primero el SQL en Neon.')
    else:
        # Verificar si ya existe
        existe = Usuario.query.filter_by(username='admin').first()
        if existe:
            print('El usuario admin ya existe')
        else:
            admin = Usuario(username='admin', id_rol=rol_gerente.id_rol)
            admin.set_password('admin123')  # Cambia esta contraseña después
            db.session.add(admin)
            db.session.commit()
            print('Usuario admin creado correctamente')
            print('Usuario: admin')
            print('Contraseña: admin123')
