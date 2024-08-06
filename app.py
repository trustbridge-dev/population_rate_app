from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import requests
#Import Pika for RabbitMQ
import pika
import os

# Initialize the database
db = SQLAlchemy()

# Define the PopulationData model
class PopulationData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    population = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

# Function to create the Flask application
def create_app(testing=False):
#Factory pattern for creating a Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///population.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if testing:
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_population.db'

    db.init_app(app)

    # Create the database tables
    with app.app_context():
        db.create_all()

    # Register routes with the app
    register_routes(app)

    return app


#Create an app instance for Gunicorn
def register_routes(app):
#Register routes with the Flask app.
    @app.route('/update_population_data')
    def update_population_data():
        data = fetch_population_data()
        for entry in data:
            monthly_population = entry['population'] // 12
            for month in range(1, 13):
                existing_record = PopulationData.query.filter_by(year=entry['year'], month=month).first()
                if existing_record:
                    existing_record.population = monthly_population
                else:
                    new_record = PopulationData(year=entry['year'], month=month, population=monthly_population)
                    db.session.add(new_record)
        db.session.commit()
        #Publish a message to RabbitMQ
        publish_message('population_updates','Population data updated')


        return jsonify({"message": "Population data updated successfully"}), 200
    
    #Route to create the Analysis
    @app.route('/get_analysis')
    def get_analysis():
        result = get_yearly_averages()
        return jsonify(result)

    @app.route('/')
    def index():
        return render_template('index.html')
    
    #Create a Health check point
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok"}), 200

    #Create a metrics route
    @app.route('/metrics')
    def metrics():
    #Return application metrics
        total_entries = PopulationData.query.count()
        total_population = db.session.query(db.func.sum(PopulationData.population)).scalar()
        unique_years = db.session.query(PopulationData.year).distinct().count()

        metrics_data = {
            "total_entries": total_entries,
            "total_population": total_population,
            "unique_years": unique_years
        }
        return jsonify(metrics_data)
    
def fetch_population_data():
    url = "https://datausa.io/api/data?drilldowns=Nation&measures=Population"
    response = requests.get(url)
    data = response.json()

    # Filter data to include only years between 2013 and 2020
    filtered_data = [
        {
            'year': int(entry['Year']),
            'population': entry['Population']
        }
        for entry in data['data']
        if 2013 <= int(entry['Year']) <= 2020
    ]

    return filtered_data

def get_yearly_averages():
    yearly_averages = db.session.query(
        PopulationData.year,
        db.func.sum(PopulationData.population).label('total_population')
    ).group_by(PopulationData.year).all()

    result = {year: total_population for year, total_population in yearly_averages}
    return result



def publish_message(queue_name, message):
    #Publish a message to the specified RabbitMQ queue.
    rabbitmq_url = os.environ.get('CLOUDAMQP_URL')
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # Declare a queue
    channel.queue_declare(queue=queue_name, durable=True)

    # Publish a message
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )

    print(f" [x] Sent {message}")
    connection.close()



if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

