from argparse import Action
from flask import Flask, request, render_template, redirect, url_for, session
from pymongo import MongoClient
import hashlib
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = b'$\x94\xd3x&\xaf\x06\x8e>\x88d\x82\xec\xd7a\xe7jz\x88\xbf\xa2\xc93\x81'  
# Replace with your generated secret key

# MongoDB connection string
client = MongoClient('mongodb://127.0.0.1:27017/')

# Select the database
db = client['mydatabase']

# Select the collections
users_collection = db['users']
crops_collection = db['crops']

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login/<role>')
def login(role):
    session['role'] = role
    return redirect(url_for('login_form'))

@app.route('/login_form.html', methods=['GET', 'POST'])
def login_form():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user = users_collection.find_one({'username': username, 'password': password})
        
        if user:
            session['username'] = username
            session['role'] = user['role']
            if user['role'] == 'farmer':
                return redirect(url_for('selection_form'))
            else:
                return redirect(url_for('customer'))
        else:
            return redirect(url_for('signup_form'))

    return render_template('login_form.html')

@app.route('/signup.html', methods=['GET', 'POST'])
def signup_form():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        email = request.form['email']
        phone = request.form['phone']
        
        user_document = {
            "role": role,
            "username": username,
            "password": password,
            "email": email,
            "phone": phone
        }
        
        users_collection.insert_one(user_document)
        session['username'] = username
        session['role'] = role
        
        if role == 'farmer':
            return redirect(url_for('selection_form'))
        else:
            return redirect(url_for('customer_page'))
    
    return render_template('signup.html')

@app.route('/selection_form', methods=['GET', 'POST'])
def selection_form():
    if request.method == 'POST':
        print("Received a POST request")
        button_value = request.form['button']
        print("Button value:", button_value)
        if button_value == "view product":
            return redirect(url_for('customer_page'))
        elif button_value == 'add product':
            return redirect(url_for('crop_form'))
    return render_template('selection.html')


@app.route('/crop_form.html')
def crop_form():
    if 'role' in session and session['role'] == 'farmer':
        return render_template('crop_form.html')
    return redirect(url_for('index'))


@app.route('/submit_crop', methods=['POST'])
def submit_crop():
    name = request.form['name']
    cost = request.form['cost']
    image = request.form['image']
    place = request.form['place']
    quantity = request.form['quantity']
    
    crop_document = {
        "name": name,
        "cost": cost,
        "image": image,
        "place": place,
        "quantity": int(quantity)
    }
    
    crops_collection.insert_one(crop_document)
    
    products = list(crops_collection.find())
    return render_template('customer_page.html', products=products)

@app.route('/customer_page.html')
def customer_page():
    products = list(crops_collection.find())
    return render_template('customer_page.html', products=products)

@app.route('/search_product', methods=['GET'])
def search_product():
    search_query = request.args.get('search')
    products = list(crops_collection.find({"name": {"$regex": search_query, "$options": "i"}}))
    return render_template('customer_page.html', products=products)

@app.route('/buy_product', methods=['POST'])
def buy_product():
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    
    product = crops_collection.find_one({"_id": ObjectId(product_id)})
    
    if product and product['quantity'] >= quantity:
        new_quantity = product['quantity'] - quantity
        crops_collection.update_one({"_id": ObjectId(product_id)}, {"$set": {"quantity": new_quantity}})
        return f"Successfully bought {quantity} of {product['name']}!"
    else:
        return "Insufficient quantity available."

if __name__ == '__main__':
    app.run(debug=True)
