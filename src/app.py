from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST
import time
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)

# Define a Prometheus counter for tracking total requests
REQUEST_COUNTER = Counter('total_requests', 'Total number of requests')
# Define a Prometheus histogram for tracking request latency
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency in seconds')

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100))
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Integer)
    wind_speed = db.Column(db.Float)
    condition = db.Column(db.String(100))

    def __repr__(self):
        return f'<WeatherData {self.city}>'

def getWeather():
    # Replace 'YOUR_API_KEY' with your actual API key
    api_key = 'cef8def099eb3e1b90d11954a1e15125'
    city = 'Abidjan'  # Replace 'Abidjan' with the desired city
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()
    
    if data['cod'] == 200:
        weather = WeatherData(
            city=data['name'],
            temperature=data['main']['temp'],
            humidity=data['main']['humidity'],
            wind_speed=data['wind']['speed'],
            condition=data['weather'][0]['description']
        )
        return weather
    else:
        return "Error fetching weather data."


def index():
        weather = getWeather()
        print(weather)
        db.session.add(weather)
        db.session.commit()
        REQUEST_COUNTER.inc()
        time.sleep(0.5)
        return f"Weather data for {weather.city} successfully stored in the database."

# Metrics endpoint
@app.route('/metrics', methods=['GET'])
def metrics():
    # Prometheus generates the metrics in a specific format
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/health', methods=['GET'])
def health_check():
    response = {
        "status": "OK",
        "message": "Service is running",
    }
    return jsonify(response), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)