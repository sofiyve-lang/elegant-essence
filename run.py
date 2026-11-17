from app import create_app

app = create_app()

if __name__ == '__main__':
  # Esto le dice a Flask que abra el servidor a cualquier dispositivo de la red
  app.run(host='0.0.0.0', port=5000, debug=True)
