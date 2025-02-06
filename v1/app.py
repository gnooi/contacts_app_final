import os
import json

from flask import (Flask, 
                   render_template,
                   url_for,
                   flash, 
                   redirect)

app = Flask(__name__)

def get_data_path():
    current_dir = os.path.dirname(__file__)

    if app.config['TESTING']:
        return os.path.join(current_dir, 'tests')
    else:
        return os.path.join(current_dir, 'contacts', 'data' )
        
def load_contacts():
    data_dir = get_data_path()

    contacts_file_path = os.path.join(data_dir, 'contacts.json')

    if os.path.exists(contacts_file_path):
        with open(contacts_file_path, "r") as file:
            contacts_data = json.load(file)
        return contacts_data
    else:
        return {}
    
@app.route("/")
def index():
    contacts_data = load_contacts()
    categories = list(contacts_data.keys())
    return render_template("home.html", categories=categories)

@app.route("/categories/<category>")
def categories(category):
    contacts_data = load_contacts()
    categories = list(contacts_data.keys())
    contacts = contacts_data.get(category, [])

    if not contacts:
        flash(f"No contacts found for {category}.")
        return redirect(url_for("index"))
    
    return render_template("categories.html", 
                           title=category, 
                           contacts=contacts, 
                           categories=categories,
                           ctgry=category)

@app.route("/contact/<name>")
def contact_info(name):
    contacts_data = load_contacts()
    all_contacts = {contact: details
                    for category, contacts in contacts_data.items()
                    for contact, details in contacts.items()}
    
    contact_details = all_contacts.get(name)

    if not contact_details:
        flash(f"No contact found for {name}.")
        return redirect(url_for("index"))
    
    return render_template("contactinfo.html", contact=contact_details, name=name)


if __name__ == "__main__":
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)