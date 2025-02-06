import os
import json
import re

from flask import (Flask, 
                   render_template,
                   url_for,
                   flash, 
                   redirect, 
                   request)

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
    return render_template("add_contact.html")

@app.route("/add_contact", methods=["POST"])
def add_contact():
    contacts_data = load_contacts()

    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    category = request.form.get("category")

    if not (name and category):
        flash("Name and category are required!", "error")
        return render_template("add_contact.html", 
                                name=name,
                                email=email,
                                phone=phone,
                                category=category)
    
    if not re.match("^[A-Za-z ]+$", name):
        flash("Name must only contain alphabetic characters and spaces.", "error")
        return render_template("add_contact.html", 
                                name=name,
                                email=email,
                                phone=phone,
                                category=category)
    
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash("Please enter a valid email address.", "error")
        return render_template("add_contact.html", 
                                name=name,
                                email=email,
                                phone=phone,
                                category=category)

    if phone and not re.match(r"^\d{3}-\d{3}-\d{4}$", phone):
        flash("Phone number must be in the format 123-456-7890.", "error")
        return render_template("add_contact.html", 
                                name=name,
                                email=email,
                                phone=phone,
                                category=category)
    
    category = category.strip().title()

    if category not in contacts_data:
        contacts_data[category] = []

    contacts_data[category].append({"name": name, "email": email, "phone": phone})

    save_contacts(contacts_data)

    flash(f"{name} was added.", "success")
    return redirect(url_for("index"))

@app.route("/contact/<name>")
def contact_info(name):
    contacts_data = load_contacts()
    all_contacts = {contact['name']: contact
                    for category, contacts in contacts_data.items()
                    for contact in contacts}

    contact_details = all_contacts.get(name)

    if not contact_details:
        flash(f"No contact found for {name}.")
        return redirect(url_for("index"))
    
    return render_template("contactinfo.html", contact=contact_details, name=name)

@app.route("/categories/<category>")
def categories(category):
    contacts_data = load_contacts()

    if category not in contacts_data:
        flash(f"No contacts found for {category}.", "error")
        return redirect(url_for("index"))
    
    contacts = contacts_data[category]

    categories = contacts_data.keys()
    
    return render_template("categories.html",
                           title=category, 
                           contacts=contacts,
                           categories=categories)

@app.route("/edit_contact/<category>/<name>", methods=["GET"])
def edit_contact_form(category, name):
    contacts_data = load_contacts()

    contact = next((c 
                    for c in contacts_data[category] 
                    if c['name'] == name), None)
    
    if not contact:
        flash("Contact not found!", "error")
        return redirect(url_for("index"))
    
    return render_template("edit_contact.html", 
                           category=category, 
                           name=contact['name'],
                           email=contact.get('email', ''),
                           phone=contact.get('phone', ''))

@app.route("/update_contact/<category>/<name>", methods=["POST"])
def update_contact(category, name):
    contacts_data = load_contacts()

    contact = next((c 
                    for c in contacts_data[category]
                    if c['name'] == name), None)
    
    if not contact:
        flash("Contact not found!", "error")
        return redirect(url_for("edit_contact_form",
                                category=category,
                                name=name))
    
    new_name = request.form.get("name")
    new_email = request.form.get("email")
    new_phone = request.form.get("phone")
    new_category = request.form.get("category")

    if not (new_name and new_category):
        flash("Name and category are required!", "error")
        return render_template("edit_contact.html", 
                                category=category,
                                name=name,
                                phone=new_phone,
                                email=new_email)
    
    if not re.match("^[A-Za-z ]+$", new_name):
        flash("Name must only contain alphabetic characters and spaces.", "error")
        return render_template("edit_contact.html", 
                                category=category,
                                name=name,
                                phone=new_phone,
                                email=new_email)
    
    if new_email and not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
        flash("Please enter a valid email address.", "error")
        return render_template("edit_contact.html", 
                                category=new_category,
                                name=new_name,
                                phone=new_phone,
                                email=new_email)

    if new_phone and not re.match(r"^\d{3}-\d{3}-\d{4}$", new_phone):
        flash("Phone number must be in the format 123-456-7890.", "error")
        return render_template("edit_contact.html", 
                                category=new_category,
                                name=new_name,
                                phone=new_phone,
                                email=new_email)
                                
    if new_category != category:
        contacts_data[category].remove(contact)

        if new_category not in contacts_data:
            contacts_data[new_category] = []

        contacts_data[new_category].append({
            "name": new_name,
            "email": new_email,
            "phone": new_phone
        })
    else:
        contact['name'] = new_name
        contact['email'] = new_email
        contact['phone'] = new_phone

    save_contacts(contacts_data)

    flash("Contact updated.", "success")
    return redirect(url_for('categories', 
                            category=new_category,
                            name=new_name, 
                            phone=new_phone,
                            email=new_email))

@app.route("/delete_contact/<category>/<name>")
def delete_contact(category, name):
    contacts_data = load_contacts()
    
    contacts_data[category] = [
        c for c in contacts_data[category]
        if c['name'] != name
    ]
    
    if not contacts_data[category]:
        del contacts_data[category]
        flash(f"{name} has been deleted from {category}", "success")
    else:
        flash(f"{name} has been deleted from {category}", "success")
    
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
    flash(f"{category} deleted.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)