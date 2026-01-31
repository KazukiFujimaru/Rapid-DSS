from flask import Flask
from handlers.routes import configure_routes

app = Flask(__name__)
# Kunci rahasia untuk session (wajib agar session/data aman)
app.secret_key = 'kunci_rahasia_rit_project'

configure_routes(app)

if __name__ == "__main__":
    # Debug=True agar kalau error kelihatan detailnya di browser
    app.run(debug=True, port=5000)