from flask import Flask
from handlers.routes import configure_routes

app = Flask(__name__)
app.secret_key = 'rapid_dss_key'

configure_routes(app)

if __name__ == "__main__":
    # Debug=True agar kalau error kelihatan detailnya di browser
    app.run(debug=True, port=5000)