from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import requests

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
        return jsonify({"message": "Population data updated successfully"}), 200
    #Route to create the Analysis
    @app.route('/get_analysis')
    def get_analysis():
        result = get_yearly_averages()
        return jsonify(result)

    @app.route('/')
    def index():
        return render_template('index.html')
    



    
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

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

