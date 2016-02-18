from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Service, Contact, Profile, Album
from flask import session as login_session
import random
import string


from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


app = Flask(__name__)

engine = create_engine('sqlite:///seniorcaredirectory.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/service/<int:service_id>/contact/json')
def serviceJSON(service_id):
    service = session.query(Service).filter_by(id = service_id).one()
    items = session.query(Contact).filter_by(service_id = service_id).all()
    return jsonify(Contacts=[i.serialize for i in items])

@app.route('/service/<int:service_id>/contact/<int:contact_id>/json/')
def contactJSON(service_id, contact_id):
    contact = session.query(Contact).filter_by(id = contact_id).one()
    return jsonify(Contact = contact.serialize)

@app.route('/')
def index():
    service = session.query(Service).filter_by(id=Service.id).all()
    return render_template('service.html', service=service)

@app.route('/service/<int:service_id>/')
def serviceDisplay(service_id):
    service = session.query(Service).filter_by(id=service_id).one()
    items = session.query(Contact).filter_by(service_id=service.id)
    details = session.query(Profile).filter_by(service_id=service.id)
    return render_template('contact.html', service=service, items=items, details=details)

# Create route for profile creation 
@app.route('/new_service/', methods=['GET','POST'])
def newService(service_id):
    if request.method == 'POST':
        newItem = Contact(name = request.form['name'])
        session.add(newItem)
        session.commit()
        flash("Service Name Added")
        return redirect(url_for('newContact', service_id = service_id))
    else:
        return render_template('newservice.html', service_id = service_id)

# Continue to contact information submission
@app.route('/service/<int:service_id>/new_contact/', methods=['GET','POST'])
def newContact(service_id):
    if request.method == 'POST':
        newItem = Contact(phone = request.form['phone'], email = request.form['email'],
                        website = request.form['website'], 
                        address = request.form['address'], city = request.form['city'],
                        state = request.form['state'], service_id = service_id)
        session.add(newItem)
        session.commit()
        flash("Contact Information Complete")
        return redirect(url_for('newContact', service_id = service_id))
    else:
        return render_template('newcontact.html', service_id = service_id)

# Finally add profile information.
@app.route('/service/<int:service_id>/new_profile/', methods=['GET','POST'])
def newProfile(service_id):
    if request.method == 'POST':
        newItem = Contact(description = request.form['description'], price_range_min = request.form['pr_min'],
                        price_range_max = request.form['pr_max'], service_id = service_id)
        session.add(newItem)
        session.commit()
        flash("Your community profile has been added!")
        return redirect(url_for('index', service_id = service_id))
    else:
        return render_template('newmenuitem.html', service_id = service_id)


# Task 2: Create route for edit[service, contact, profile] functions here
@app.route('/service/service-<int:service_id>/edit/', methods = ['GET', 'POST'])
def editService(service_id):
    editedItem = session.query(Service).filter_by(id = id).one()
    if request.method == 'POST':
        editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        flash("Your service name has been edited.")
        return redirect(url_for('serviceDisplay', service_id = service_id))
    else: 
        return render_template('editedservice.html', service_id = service_id, i = editedItem)

@app.route('/service/<int:service_id>/contact-<int:contact_id>/edit/', methods = ['GET', 'POST'])
def editContact(service_id, contact_id):
    editedItem = session.query(Contact).filter_by(id = contact_id).one()
    if request.method == 'POST':
        editedItem.phone = request.form['phone']
        editedItem.email = request.form['email']
        editedItem.website = request.form['website'], 
        editedItem.address = request.form['address']
        editedItem.city = request.form['city']
        editedItem.state = request.form['state']
        editedItem.zipcode = request.form['zipcode']
        session.add(editedItem)
        session.commit()
        flash("Your menu item has been edited.")
        return redirect(url_for('serviceDisplay', service_id = service_id))
    else: 
        return render_template('editedcontact.html', service_id = service_id, contact_id = contact_id, i = editedItem)

@app.route('/service/<int:service_id>/profile-<int:profile_id>/edit/', methods = ['GET', 'POST'])
def editProfile(service_id, profile_id):
    editedItem = session.query(Profile).filter_by(id = profile_id).one()
    if request.method == 'POST':
        editedItem.description = request.form['description']
        editedItem.price_range_min = request.form['pr_min']
        editedItem.price_range_max = request.form['pr_max']
        session.add(editedItem)
        session.commit()
        flash("Your profile information has been edited.")
        return redirect(url_for('serviceDisplay', service_id = service_id))
    else: 
        return render_template('editedprofile.html', service_id = service_id, profile_id = profile_id, i = editedItem)


# Task 3: Create a route for deleteService function here
@app.route('/service/<int:service_id>/delete/', methods = ['GET','POST'])
def deleteService(service_id):
    deletedItem = session.query(Service).filter_by(id = id).one()
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash("Your service has been deleted from our database.")
        return redirect(url_for('index', service_id = service_id))
    else:
        return render_template('deleteservice.html', service_id = service_id, item = deletedItem)

if __name__ == '__main__':
    app.secret_key = 'key1'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)