from flask import Flask, request, redirect, render_template, flash, session
from mysqlconnection import MySQLConnector
from flask_bcrypt import Bcrypt
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "Donttellanyone"
mysql = MySQLConnector(app, 'wall')

@app.route('/')
def index(): 
	return render_template('index.html')

@app.route('/register', methods=['POST'])
def validate(): 
	first_name = request.form['first_name']
	last_name = request.form['last_name']
	email = request.form['email']
	password = request.form['password']
	password_confirmation = request.form['password_confirmation']
	pw_hash = bcrypt.generate_password_hash(password)

	if len(first_name) < 1: 
		flash('First Name cannot be empty!')
	elif len(last_name) < 1: 
		flash('Last Name cannot be empty!')
	elif not EMAIL_REGEX.match(email): 
		flash("Email is not valid!")
	elif len(password) < 8: 
		flash("Password must be at least 8 characters!")
	elif password != password_confirmation: 
		flash("Passwords do not match!")
	else: 
		query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"
		data = {
			'first_name': first_name, 
			'last_name': last_name, 
			'email': email, 
			'password': pw_hash
		}
		mysql.query_db(query, data)
		flash('Successfully registered new user!  Please login to access THE WALL!')
	
	return redirect('/')

@app.route('/login', methods=['POST'])
def login(): 
	email = request.form['email']
	password = request.form['password']
	
	query = "SELECT * FROM users WHERE email = :email LIMIT 1"
	data = {
		'email': email
	}
	user = mysql.query_db(query, data)
	
	if bcrypt.check_password_hash(user[0]['password'], password): 
		session['id'] = user[0]['id']
		return redirect('/dashboard')
	else: 
		flash('Email/Password do not match! Try again!')
		return redirect('/')

@app.route('/dashboard', methods=['GET'])
def dashboard(): 
	
	query = "SELECT * FROM users WHERE id = :id LIMIT 1"
	data = {
		'id': session['id']
	}
	user = mysql.query_db(query, data)
	mquery = "SELECT first_name, last_name, users.id AS user_id, message, messages.created_at AS posted_date, messages.id AS message_id, messages.user_id AS mu_id FROM users LEFT JOIN messages ON users.id = messages.user_id ORDER BY posted_date DESC"
	messages = mysql.query_db(mquery)
	cquery = "SELECT first_name, last_name, messages.id AS message_id, comment, comments.created_at as comment_date FROM comments LEFT JOIN messages on comments.message_ID = messages.id LEFT JOIN users on comments.user_id = users.id ORDER BY comment_date DESC"
	comments = mysql.query_db(cquery) 

	return render_template('dashboard.html', user=user, messages = messages, comments = comments)

@app.route('/logout')
def logout(): 
	session.clear()
	return redirect('/')

@app.route('/post_message', methods=['POST'])
def message(): 
	message = request.form['message']
	user_id = request.form['user_id']
	query = "INSERT INTO messages (message, created_at, updated_at, user_id) VALUES (:message, NOW(), NOW(), :user_id)" 
	data = {
		'message': message, 
		'user_id': user_id
	}
	mysql.query_db(query, data)
	
	return redirect('/dashboard')

@app.route('/post_comment', methods=['POST'])
def comment():
	comment = request.form['comment']
	user_id = request.form['user_id']
	message_id = request.form['message_id']
	query = "INSERT INTO comments (comment, created_at, updated_at, message_id, user_id) VALUES (:comment, NOW(), NOW(), :message_id, :user_id)"
	data = {
		'comment': comment, 
		'message_id': message_id,
		'user_id': user_id
	}
	mysql.query_db(query, data)
	
	return redirect('/dashboard')

@app.route('/destroy/<comments_id>', methods=['POST'])
def delete(comments_id):
	query = "DELETE FROM comments WHERE id = :id"
	data = {'id': message_id}
	mysql.query_db(query, data)
	return redirect('/dashboard')

app.run(debug = True)