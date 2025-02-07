import os
import json
import re

from flask import (Flask, 
                   render_template,
                   url_for,
                   flash, 
                   redirect, 
                   request, 
                   session)

app = Flask(__name__)
app.secret_key='secret1'

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
    
def save_contacts(contacts_data):
    data_dir = get_data_path()
    contacts_file_path = os.path.join(data_dir, 'contacts.json')

    with open(contacts_file_path, "w") as file:
        json.dump(contacts_data, file, indent=4)

def validate_contact_form(new_name, new_category, new_email, new_phone):
    if not (new_name and new_category):
        return "Name and category are required!"
    
    if not re.match("^[A-Za-z ]+$", new_name):
        return "Name must only contain alphabetic characters and spaces."
    
    if new_email and not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
        return "Please enter a valid email address."
    
    if new_phone and not re.match(r"^\d{3}-\d{3}-\d{4}$", new_phone):
        return "Phone number must be in the format 123-456-7890."
    
    return None  
    
@app.route("/")
def index():
    contacts_data = load_contacts()
    all_contacts = []
    
    for category, contacts in contacts_data.items():
        all_contacts.extend(contacts)

    categories = list(contacts_data.keys())
    return render_template("home.html", 
                           categories=categories, 
                           contacts=all_contacts)

@app.route("/add_contact", methods=["GET"])
def add_contact_page():
    form_data = session.pop('form_data', {})
    return render_template("add_contact.html", 
                         name=form_data.get('name', ''),
                         email=form_data.get('email', ''),
                         phone=form_data.get('phone', ''),
                         category=form_data.get('category', ''))

@app.route("/add_contact", methods=["POST"])
def add_contact():
    contacts_data = load_contacts()
    
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    category = request.form.get("category")
    
    session['form_data'] = {
        'name': name,
        'email': email,
        'phone': phone,
        'category': category
    }

    error_message = validate_contact_form(name, category, email, phone)
    
    if error_message:
        flash(error_message, "error")
        return redirect(url_for('add_contact_page'))
    
    category = category.strip().title()
    
    original_contact = session.pop('original_contact', None)
    if original_contact:
        old_category = original_contact['category']
        if old_category in contacts_data:
            contacts_data[old_category] = [
                c for c in contacts_data[old_category]
                if c['name'] != original_contact['name']
            ]
            if not contacts_data[old_category]:
                del contacts_data[old_category]
    
    if category not in contacts_data:
        contacts_data[category] = []
    
    contacts_data[category].append({
        "name": name,
        "email": email,
        "phone": phone
    })

    save_contacts(contacts_data)
    
    session.pop('form_data', None)
    
    flash(f"{name} was {'updated' if original_contact else 'added'}.", "success")
    return redirect(url_for('categories', category=category))

@app.route("/edit_contact/<category>/<name>", methods=["GET"])
def edit_contact_form(category, name):
    contacts_data = load_contacts()
    
    contact_list = contacts_data.get(category, [])
    contact = next((c for c in contact_list if c['name'] == name), None)
    
    if not contact:
        flash("Contact not found!", "error")
        return redirect(url_for("index"))
    
    session['original_contact'] = {
        'name': name,
        'category': category
    }
    
    session['form_data'] = {
        'name': contact['name'],
        'email': contact.get('email', ''),
        'phone': contact.get('phone', ''),
        'category': category
    }
    
    return redirect(url_for('add_contact_page'))

@app.route("/update_contact/<category>/<name>", methods=["POST"])
def update_contact(category, name):
    session['original_contact'] = {
        'name': name,
        'category': category
    }
    return redirect(url_for('add_contact'), code=307)  # 307 preserves POST method



@app.route("/contact/<name>")
def contact_info(name):
    contacts_data = load_contacts()
    all_contacts = {contact['name']: contact
                    for category, contacts in contacts_data.items()
                    for contact in contacts}

    contact_details = all_contacts.get(name)

    # if not contact_details:
    #     flash(f"No contact found for {name}.")
    #     return redirect(url_for("index"))
    
    return render_template("contactinfo.html", contact=contact_details, name=name)

@app.route("/categories/<category>")
def categories(category):
    contacts_data = load_contacts()

    # if category not in contacts_data:
    #     flash(f"No contacts found for {category}.", "error")
    #     return redirect(url_for("index"))
    
    contacts = contacts_data[category]

    categories = contacts_data.keys()
    
    return render_template("categories.html",
                           title=category, 
                           contacts=contacts,
                           categories=categories)

@app.route("/delete_contact/<category>/<name>")
def delete_contact(category, name):
    contacts_data = load_contacts()

    # if category not in contacts_data:
    #     flash(f"{category} does not exist.", "error")
    #     return redirect(url_for("index"))
    
    contacts_data[category] = [
        c for c in contacts_data[category]
        if c['name'] != name
    ]
    
    if not contacts_data[category]:
        del contacts_data[category]

    flash(f"{name} has been deleted from {category}.", "success")
    
    save_contacts(contacts_data)
    
    if category in contacts_data:
        return redirect(url_for('categories', category=category))
    else:
        return redirect(url_for("index"))

@app.route("/delete_category/<category>")
def delete_category(category):
    contacts_data = load_contacts()
    remaining_contacts_data = {c: contacts 
                     for c, contacts in contacts_data.items() 
                     if c != category}

    save_contacts(remaining_contacts_data)
    flash(f"{category} has been deleted.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)