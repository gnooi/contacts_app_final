import unittest 
import shutil
import os
import json
from app import app, load_contacts

class ContactsTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.data_path = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_path, exist_ok=True)

        with open(os.path.join(self.data_path, 'contacts.json'), 'w') as file:
            json.dump({}, file)

    def tearDown(self):
        shutil.rmtree(self.data_path, ignore_errors=True)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Contacts', html)
        self.assertIn('+', html)

    def test_add_contact_page_loads(self):
        response = self.client.get('/add_contact')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Add a New Contact', response.get_data(as_text=True))

    def test_add_contact_to_empty_app(self):
        new_contact = {
            "name": "Bob",
            "email": "Bob@example.com",
            "phone": "555-666-7777",
            "category": "Friends"
        }

        response = self.client.post('/add_contact', data=new_contact, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Bob was added.', html)
        self.assertIn('Friends', html)

    def test_view_contact_details(self):
        contact = {
            "name": "Bob",
            "email": "Bob@example.com",
            "phone": "555-666-7777",
            "category": "Friends"
        }

        self.client.post('/add_contact', data=contact, follow_redirects=True)

        response = self.client.get('/contact/Bob')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn('Bob', html)
        self.assertIn('Bob@example.com', html)
        self.assertIn('555-666-7777', html)

    def test_edit_contact_form(self):

        with self.client as client:
            response = client.get('/edit_contact/Friends/Bob')

            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/add_contact')

            with client.session_transaction() as session:
                self.assertEqual(
                    session['original_contact'], 
                    {'name': 'Bob', 'category': 'Friends'}
                )
                self.assertEqual(
                    session['form_data'],
                    {
                        "name": "Bob",
                        "email": "Bob@example.com",
                        "phone": "111-222-3333",
                        "category": "Friends"
                    }
                )
    
    def test_update_contact_missing_name_and_category(self):
        contact = {
            "name": "",
            "email": "Bob@example.com",
            "phone": "123-456-7890",
            "category": "Friends"
        }

        response = self.client.post('/update_contact/Friends/Bob', data=contact, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Name and category are required!", html)
        self.assertEqual(response.status_code, 200)

    def test_update_contact_invalid_name(self):
        contact = {
            "name": "Bob123",
            "email": "Bob@example.com",
            "phone": "123-456-7890",
            "category": "Friends"
        }

        response = self.client.post('/update_contact/Friends/Bob', data=contact, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Name must only contain alphabetic characters and spaces.", html)
        self.assertEqual(response.status_code, 200)

    def test_update_contact_invalid_email(self):
        contact = {
            "name": "Bob",
            "email": "Bob-at-example.com",
            "phone": "123-456-7890",
            "category": "Friends"
        }
        response = self.client.post('/update_contact/Friends/Bob', data=contact, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Please enter a valid email address.", html)
        self.assertEqual(response.status_code, 200)

    def test_update_contact_invalid_phone(self):
        contact = {
            "name": "Bob",
            "email": "Bob@example.com",
            "phone": "1234567890",
            "category": "Friends"
        }

        response = self.client.post('/update_contact/Friends/Bob', data=contact, follow_redirects=True)
        html = response.get_data(as_text=True)
        self.assertIn("Phone number must be in the format 123-456-7890.", html)
        self.assertEqual(response.status_code, 200) 

    def test_delete_contact(self):
        contact = {
            "name": "Daisy",
            "email": "daisy@example.com",
            "phone": "777-888-9999",
            "category": "Friends"
        }
        self.client.post('/add_contact', data=contact, follow_redirects=True)
        
        response = self.client.get('/delete_contact/Friends/Daisy', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        html = response.get_data(as_text=True)
        self.assertIn('Daisy has been deleted from Friends.', html)

    def test_delete_category(self):
        contacts_data = {
            "Friends": [
            {
            "name": "Daisy",
            "email": "daisy@example.com",
            "phone": "777-888-9999"}, 
            {
            "name": "Xiaowen", 
            "email": "Xiaowen@example.com",
            "phone": "111-222-3333"}

        ], 
            "Work":[
                {
                "name": "Bob", 
                "email": "Bob@example.com",
                "phone": "333-444-555"
                }

            ]
        }
        
        self.client.post('/delete_category', data=contacts_data, follow_redirects=True)
        response = self.client.get('/delete_category/Work', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('Work has been deleted.', html)
        
if __name__ == "__main__":
    unittest.main()