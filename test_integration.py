import unittest
from unittest.mock import patch
from app import create_app, db, PopulationData
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
#Set up a test client and database for integration testing
        self.app = create_app(testing=True)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
#Clean up the test database.
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.fetch_population_data')
    def test_integration_flow(self, mock_fetch_population_data):
#Test the integration flow of updating and analyzing data
        # Define mock data for the external API
        mock_data = [
            {'year': 2013, 'population': 18000},
            {'year': 2014, 'population': 24000}
        ]

        # Configure the mock to return the mock data
        mock_fetch_population_data.return_value = mock_data

        # Simulate a request to update the population data
        response_update = self.client.get('/update_population_data')
        self.assertEqual(response_update.status_code, 200)
        self.assertIn(b'Population data updated successfully', response_update.data)

        # Check if the database is populated correctly
        for data in mock_data:
            year = data['year']
            expected_population = data['population']
            total_population = db.session.query(db.func.sum(PopulationData.population)).filter_by(year=year).scalar()
            self.assertEqual(total_population, expected_population)

        # Simulate a request to get the yearly analysis
        response_analysis = self.client.get('/get_analysis')
        self.assertEqual(response_analysis.status_code, 200)

        # Verify the analysis result
        analysis_result = response_analysis.get_json()
        # Convert keys to integers for comparison
        analysis_result = {int(year): population for year, population in analysis_result.items()}
        expected_analysis = {2013: 18000, 2014: 24000}
        self.assertEqual(analysis_result, expected_analysis)

        # Test the /metrics endpoint
        response_metrics = self.client.get('/metrics')
        self.assertEqual(response_metrics.status_code, 200)

        # Verify the metrics result
        metrics_result = response_metrics.get_json()
        expected_metrics = {
            "total_entries": 24,   # 2 years * 12 months
            "total_population": 42000,  # 18000 + 24000
            "unique_years": 2
        }
        self.assertEqual(metrics_result, expected_metrics)

if __name__ == '__main__':
    unittest.main()

