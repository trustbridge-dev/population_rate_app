import unittest
from unittest.mock import patch
from app import create_app, db, PopulationData, get_yearly_averages

class YearlyAveragesTestCase(unittest.TestCase):
    def setUp(self):
#Set up a test database and populate it with test data
        self.app = create_app(testing=True)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
#Clean up the test database
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.publish_message')
    @patch('app.fetch_population_data')
    def test_update_population_data_with_mock_messaging(self, mock_fetch_population_data, mock_publish_message):
        #Test the get_yearly_averages function using mock data
        # Define mock data
        mock_data = [
            {'year': 2013, 'population': 18000},  # Monthly average will be 1500
            {'year': 2014, 'population': 24000}   # Monthly average will be 2000
        ]

        # Configure the mock to return this data
        mock_fetch_population_data.return_value = mock_data
        mock_publish_message.return_value = None

        # Call the function that uses fetch_population_data
        response = self.app.test_client().get('/update_population_data')

        # Assert the response from the update_population_data endpoint
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Population data updated successfully', response.data)


        #Verify that the publish_message function was called
        mock_publish_message.assert_called_once_with('population_updates','Population data updated')


        # Now test the yearly averages
        expected_results = {
            2013: 18000,
            2014: 24000
        }

        # Calculate the yearly averages after the data is updated
        yearly_averages = get_yearly_averages()
        self.assertEqual(yearly_averages, expected_results)

if __name__ == '__main__':
    unittest.main()

