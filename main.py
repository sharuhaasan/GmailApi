import unittest
from unittest.mock import patch, Mock, mock_open
import datetime
from Gmail_Api import (
    authenticate_gmail_api,
    convert_to_mysql_datetime,
    insert_email,
    load_rules_from_json,
    apply_rules_to_emails,
    apply_condition,
    apply_actions,
    mark_email_as_read,
    move_email_to_folder,
)

# Remove the unnecessary import of DB_CONFIG since it's not used in this test file.

class TestYourProjectFunctions(unittest.TestCase):

    @patch('Gmail_Api.build')
    @patch('builtins.open', new_callable=mock_open)
    @patch('Gmail_Api.pickle', autospec=True)
    def test_authenticate_gmail_api(self, mock_pickle, mock_open_file, mock_build):
        # Create and configure a mock for credentials
        mock_credentials = Mock(valid=True)
        mock_pickle.load.return_value = mock_credentials

        # Call the function to authenticate
        service = authenticate_gmail_api()

        # Assert that the mock build method was called with the mock credentials
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_credentials)

    def test_convert_to_mysql_datetime(self):
        # Test case for a valid timestamp
        timestamp = 1695970800000
        expected_result = '2023-09-29 12:30:00'
        result = convert_to_mysql_datetime(timestamp)
        self.assertEqual(result, expected_result)

        # Test case for a None timestamp
        result = convert_to_mysql_datetime(None)
        self.assertIsNone(result)

        # Add more test cases as needed

    @patch('mysql.connector.connect')
    @patch('mysql.connector.Error')
    def test_insert_email(self, mock_error, mock_connect):
        # Mock database connection and cursor
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.is_connected.return_value = True
        mock_cursor.execute.return_value = None
        mock_connect.return_value = mock_connection

        # Test data
        email_data = ('Test Subject', 'Test Sender', '2023-09-29 12:30:00', 'Test Body', 'Test Message ID')

        # Call the function
        insert_email(email_data)

    @patch('Gmail_Api.apply_condition')
    @patch('Gmail_Api.apply_actions')
    def test_apply_rules_all_true(self, mock_apply_actions, mock_apply_condition):
        # Mock data
        emails = [
            {'sender': 'test@example.com', 'subject': 'Important Email', 'body': 'Body',
             'internal_date': '2023-09-28 14:30:00', 'message_id': '123'}
        ]
        rules = [
            {
                'predicate': 'All',
                'conditions': [{'field': 'Subject', 'predicate': 'Contains', 'value': 'Important'}],
                'actions': [{'action': 'Mark as Read'}]
            }
        ]

        # Mock the condition and action results
        mock_apply_condition.return_value = True
        mock_apply_actions.return_value = None

        # Call the function
        apply_rules_to_emails(emails, rules)

        # Assert that apply_condition and apply_actions were called correctly
        mock_apply_condition.assert_called_once()
        mock_apply_actions.assert_called_once()
        self.assertEqual(mock_apply_actions.call_args[0][0]['message_id'], '123')
        self.assertTrue('Mark as Read' in [action['action'] for action in mock_apply_actions.call_args[0][1]])

    @patch('Gmail_Api.apply_condition')
    @patch('Gmail_Api.apply_actions')
    def test_apply_rules_all_false(self, mock_apply_actions, mock_apply_condition):
        # Mock data
        emails = [
            {'sender': 'test@example.com', 'subject': 'Regular Email', 'body': 'Body',
             'internal_date': '2023-09-28 14:30:00', 'message_id': '123'}
        ]
        rules = [
            {
                'predicate': 'All',
                'conditions': [{'field': 'Subject', 'predicate': 'Contains', 'value': 'Important'}],
                'actions': [{'action': 'Mark as Read'}]
            }
        ]

        # Mock the condition result (always False)
        mock_apply_condition.return_value = False

        # Call the function
        apply_rules_to_emails(emails, rules)

        # Assert that apply_condition was called correctly
        mock_apply_condition.assert_called_once()
        mock_apply_actions.assert_not_called()

    @patch('builtins.open', new_callable=mock_open, read_data='{"rules": [{"conditions": [{"field": "Subject", "predicate": "Contains", "value": "Important"}], "actions": [{"action": "Mark as Read"}]}]}')
    def test_load_rules_from_json(self, mock_open_file):
        # Call the function
        rules = load_rules_from_json('fake_rules.json')  # Replace with your actual JSON file path

        # Assert that the function correctly loads and parses the JSON file
        expected_rules = [{'conditions': [{'field': 'Subject', 'predicate': 'Contains', 'value': 'Important'}],
                           'actions': [{'action': 'Mark as Read'}]}]
        self.assertEqual(rules, expected_rules)

    def test_apply_condition(self):
        # Test cases for apply_condition function
        # You should add more test cases for various conditions and predicates

        # Test case: Contains predicate
        email = {'field': 'Value'}
        condition = {'field': 'field', 'predicate': 'Contains', 'value': 'Val'}
        result = apply_condition(email, condition)
        self.assertTrue(result)

        # Test case: Does not Contain predicate
        condition = {'field': 'field', 'predicate': 'Does not Contain', 'value': 'Val'}
        result = apply_condition(email, condition)
        self.assertFalse(result)

        # Test case: Equals predicate
        condition = {'field': 'field', 'predicate': 'Equals', 'value': 'Value'}
        result = apply_condition(email, condition)
        self.assertTrue(result)

        # Test case: Does not Equal predicate
        condition = {'field': 'field', 'predicate': 'Does not Equal', 'value': 'Value'}
        result = apply_condition(email, condition)
        self.assertFalse(result)

        # Test case: Less than predicate (for datetime fields)
        email = {'field': datetime.datetime(2023, 9, 28, 12, 30, 00)}
        condition = {'field': 'field', 'predicate': 'Less than', 'value': '2023, 9, 29, 12, 30, 00'}
        result = apply_condition(email, condition)
        self.assertTrue(result)

        # Test case: Greater than predicate (for datetime fields)
        condition = {'field': 'field', 'predicate': 'Greater than', 'value': '2023, 9, 29, 12, 30, 00'}
        result = apply_condition(email, condition)
        self.assertFalse(result)

    def test_apply_actions(self):
        # Test cases for apply_actions function
        # You should add more test cases as needed

        # Test case: Mark as Read action
        email = {'message_id': '123'}
        action = {'action': 'Mark as Read'}
        with patch('Gmail_Api.mark_email_as_read') as mock_mark_email_as_read:
            apply_actions(email, [action])
            mock_mark_email_as_read.assert_called_once_with(email)

        # Test case: Move Message action
        action = {'action': 'Move Message', 'folder': 'Example Folder'}
        with patch('Gmail_Api.move_email_to_folder') as mock_move_email_to_folder:
            apply_actions(email, [action])
            mock_move_email_to_folder.assert_called_once_with(email, 'Example Folder')

    @patch('Gmail_Api.authenticate_gmail_api')
    @patch('Gmail_Api.logging')
    def test_mark_email_as_read(self, mock_logging, mock_authenticate_gmail_api):
        # Mock the service and its methods
        mock_service = Mock()
        mock_response = {'labelIds': []}
        mock_authenticate_gmail_api.return_value = mock_service
        mock_service.users().messages().modify.return_value.execute.return_value = mock_response

        # Test case: Marking an email as read successfully
        email = {'message_id': '123'}
        mark_email_as_read(email)
        mock_service.users().messages().modify.assert_called_once_with(
            userId='me', id='123', body={'removeLabelIds': ['UNREAD']}
        )
        mock_logging.error.assert_not_called()

    @patch('Gmail_Api.authenticate_gmail_api')  # Mock the authenticate_gmail_api function
    @patch('Gmail_Api.logging')  # Mock the logging module
    def test_move_email_to_folder_success(self, mock_logging, mock_authenticate_gmail_api):
        # Mock the service and its methods
        mock_service = Mock()
        mock_labels = {'labels': [{'name': 'Example Folder'}, {'name': 'INBOX'}]}
        mock_response = {'labelIds': ['Example Folder']}
        mock_authenticate_gmail_api.return_value = mock_service
        mock_service.users().labels().list.return_value.execute.return_value = mock_labels
        mock_service.users().messages().modify.return_value.execute.return_value = mock_response

        # Test case: Moving an email to a folder successfully
        email = {'message_id': '123'}
        move_email_to_folder(email, 'Example Folder')

        # Assertions
        mock_service.users().messages().modify.assert_called_once_with(
            userId='me', id='123', body={'addLabelIds': ['Example Folder'], 'removeLabelIds': ['INBOX']}
        )
        mock_logging.error.assert_not_called()

if __name__ == '__main__':
    unittest.main()
