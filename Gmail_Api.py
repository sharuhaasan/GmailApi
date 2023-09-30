import os
import pickle
import mysql.connector
from mysql.connector import Error
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime
import pytz
import json
import logging

# Define constants
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.labels']
CLIENT_SECRET_FILE = 'C:/Users/NSHHP/Downloads/client_secret_509730660755-rnaj4ujvaun0tvhem1qkoglt7hpgbadn.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.pickle'
RULES_FILE = 'Rules.json'
UNREAD_LABEL = 'UNREAD'

# Define database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'database': 'gmailapi',
    'user': 'root',
    'password': 'root'
}



# Function to authenticate with Gmail API
def authenticate_gmail_api():
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

# Function to convert milliseconds to a MySQL datetime string in IST
def convert_to_mysql_datetime(milliseconds):
    if not milliseconds:
        return None
    try:
        seconds = int(milliseconds) // 1000
        utc_datetime = datetime.datetime.utcfromtimestamp(seconds)
        ist_timezone = pytz.timezone('Asia/Kolkata')
        ist_datetime = utc_datetime.replace(tzinfo=pytz.utc).astimezone(ist_timezone)
        return ist_datetime.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logging.error(f"Error converting milliseconds to datetime: {e}")
        return None

# Function to insert an email into the MySQL database
def insert_email(email_data):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            cursor = connection.cursor()
            query = "INSERT INTO emails (subject, sender, internal_date, body, message_id) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, email_data)
            connection.commit()
            print("Email inserted successfully")
        else:
            logging.error("Database connection failed.")

    except Error as e:
        logging.error(f"Error: {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Function to fetch emails, process them, and insert into the database
def fetch_and_insert_emails():
    try:
        service = authenticate_gmail_api()
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=4).execute()
        messages = results.get('messages', [])

        if not messages:
            logging.info('No messages found in your Inbox.')
        else:
            for message in messages:
                message_id = message['id']
                email = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
                subject = next((header['value'] for header in email['payload']['headers'] if header['name'] == 'Subject'), 'Subject not found')
                sender = next((header['value'] for header in email['payload']['headers'] if header['name'] == 'From'), 'From not found')
                internal_date = email.get('internalDate')
                internal_date_mysql = convert_to_mysql_datetime(internal_date)
                email_data = (subject, sender, internal_date_mysql, email['snippet'], message_id)
                insert_email(email_data)

    except Exception as e:
        logging.error(f"Error fetching and inserting emails: {e}")

# Function to load rules from a JSON file
def load_rules_from_json(file_path):
    try:
        with open(file_path, 'r') as json_file:
            rules_data = json.load(json_file)
        return rules_data.get('rules', [])
    except Exception as e:
        logging.error(f"Error loading rules from JSON: {e}")
        return []

# Function to apply rules to emails
def apply_rules_to_emails(emails, rules):
    try:
        for email in emails:
            email_data = {
                'From': email['sender'],
                'Subject': email['subject'],
                'Message': email['body'],
                'Received Date/Time': email['internal_date'],
                'message_id': email['message_id']
            }
            for rule in rules:
                conditions = rule.get('conditions', [])
                actions = rule.get('actions', [])
                if rule.get('predicate') == 'All':
                    if all(apply_condition(email_data, condition) for condition in conditions):
                        apply_actions(email_data, actions)
                        print(f"Rule Applied for email: {email_data}")
                    else:
                        print(f"Rule not Applied: {rule}, Conditions not met for email: {email_data}")
                elif rule.get('predicate') == 'Any':
                    if any(apply_condition(email_data, condition) for condition in conditions):
                        apply_actions(email_data, actions)
                        print(f"Rule Applied for email: {email_data}")
                    else:
                        print(f"Rule not Applied: {rule}, Conditions not met for email: {email_data}")

    except Exception as e:
        logging.error(f"Error applying rules to emails: {e}")

def apply_condition(email, condition):
    field = condition.get('field', '')
    predicate = condition.get('predicate', '')
    value = condition.get('value', '')
    field_value = email.get(field, '')

    if field == 'Received Date/Time':
        field_value = email.get(field, datetime.datetime.min)

    if predicate == 'Contains':
        return value in field_value
    elif predicate == 'Does not Contain':
        return value not in field_value
    elif predicate == 'Equals':
        return field_value == value
    elif predicate == 'Does not Equal':
        return field_value != value
    elif predicate == 'Less than':
        target_date = datetime.datetime.strptime(value, '%Y, %m, %d, %H, %M, %S')
        return field_value < target_date
    elif predicate == 'Greater than':
        target_date = datetime.datetime.strptime(value, '%Y, %m, %d, %H, %M, %S')
        return field_value > target_date

def apply_actions(email, actions):
    try:
        for action in actions:
            action_type = action.get('action', '')

            if action_type == "Mark as Read":
                mark_email_as_read(email)

            elif action_type == "Move Message":
                folder_name = action.get('folder', '')
                move_email_to_folder(email, folder_name)

    except Exception as e:
        logging.error(f"Error applying actions to email: {e}")

def mark_email_as_read(email):
    try:
        message_id = email.get('message_id', '')
        service = authenticate_gmail_api()

        response = service.users().messages().modify(userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()

        if 'UNREAD' not in response.get('labelIds', []):
            print(f"Successfully marked email from '{email.get('From')}' as read.")
        else:
            print(f"Failed to mark email as read. API response: {response}")
    except Exception as e:
        logging.error(f"Error marking email as read: {e}")

def move_email_to_folder(email, folder_name):
    try:
        message_id = email.get('message_id', '')
        service = authenticate_gmail_api()

        labels = service.users().labels().list(userId='me').execute()
        existing_labels = [label['name'] for label in labels.get('labels', [])]

        if folder_name not in existing_labels:
            logging.error(f"Label '{folder_name}' does not exist in your Gmail account.")
            return

        modify_request = {
            'addLabelIds': [folder_name],
            'removeLabelIds': ['INBOX']
        }

        response = service.users().messages().modify(userId='me', id=message_id, body=modify_request).execute()

        if folder_name in response.get('labelIds', []):
            print(f"Successfully moved email with subject '{email.get('Subject')}' to '{folder_name}'.")
        else:
            print(f"Failed to move email to '{folder_name}'. API response: {response}")
    except Exception as e:
        logging.error(f"Exception occurred: {e}")

def fetch_emails_from_database():
    connection = None
    emails = []
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            cursor = connection.cursor()
            query = "SELECT * FROM emails"
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                email_data = {
                    'message_id': row[5],
                    'subject': row[1],
                    'sender': row[2],
                    'internal_date': row[3],
                    'body': row[4]
                }
                emails.append(email_data)

    except Error as e:
        logging.error(f"Error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
    return emails

# Main function
if __name__ == '__main__':
        service = authenticate_gmail_api()
        fetch_and_insert_emails()
        fetched_emails = fetch_emails_from_database()
        rules = load_rules_from_json(RULES_FILE)
        apply_rules_to_emails(fetched_emails, rules)
