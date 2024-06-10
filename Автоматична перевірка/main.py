from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import sqlite3
import os
import unittest 
import requests

app = Flask(__name__, template_folder='template', static_folder='static')
app.secret_key = os.urandom(24)
events = {1: "Feeding animals", 12: "Find yourself a friend", 25: "Playing with animals"}

DATABASE = 'blog.db'
admin_list = ["maxym", "Ivan"]

def create_table():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, email TEXT)')
    conn.commit()
    conn.close()

@app.route("/")
@app.route("/home")
def home():
    global events
    create_table()
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    conn.close()
    return render_template('reg.html', users=users)

@app.route("/login")
def login():
    return render_template('log.html')

@app.route("/reg")
def reg():
    return render_template('reg.html')

@app.route("/reg_user", methods=['POST', 'GET'])
def reg_user():
    if request.method == 'POST':
        username = request.form.get('name')
        password = request.form.get('password')
        email = request.form.get('email')

        if username and password and email:
            conn = sqlite3.connect(DATABASE)
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cur.fetchone()
            if user:
                problem = "This username is already registered in the database"
                return render_template('reg.html', problem=problem)
            cur.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
            conn.commit()
            conn.close()
            session['name'] = username
            return redirect(url_for('home'))
        else:
            problem = "Please fill in all fields"
            return render_template('reg.html', problem=problem)
    else:
        return render_template('reg.html')

@app.route("/login_user", methods=['POST', 'GET'])
def login_user():
    global admin_list
    if request.method == 'POST':
        username = request.form.get('name')
        password = request.form.get('password')

        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['name'] = user[1]
            return render_template('profil.html', name=user[1], email=user[3], admin_list=admin_list)
        else:
            problem = "Incorrect username or password"
            return render_template('log.html', problem=problem)
    else:
        return render_template('log.html')

@app.route("/charity")
def charity():
    return render_template('info.html')

@app.route("/calendar")
def calendar():
    return render_template('calendar.html')

@app.route("/delete_user_by/<email>")
def delete_user_by(email):
    try:
        delete_user_events_by_email(email)
        delete_user_by_email(email)
        resp_data = {"is_deleted": True}
        status = 200
    except Exception as e:
        resp_data = {"is_deleted": False, "error": str(e)}
        status = 500
    response = make_response(resp_data)
    response.status_code = status
    return response

def get_user_by(email):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE email = ?', (email))
    user = cur.fetchone()
    conn.close()
    return user

def delete_user_events_by_email(email):
    user = get_user_by(email)
    if user:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('DELETE FROM events WHERE user_id = ?', (user[0],))
        conn.commit()
        conn.close()



def delete_user_by_email(email):
    user = get_user_by(email)
    if user:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE email = ?', (email,))
        conn.commit()
        conn.close()

class TestCalendarAPI(unittest.TestCase):
    token = None

    def setUp(self):
        self.url = "http://localhost:5000"
        self.headers = {"Content-Type": "application/json"}
        self.login_data = {
            "nickname": "test_nickname",
            "password": "test_password",
            "email": "test_email@test.com"
        }

    def test_register_new_user(self):
        response = requests.post(f"{self.url}/reg_user", json=self.login_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["isAddedToDB"], True)
        response = requests.post(f"{self.url}/reg_user", json=self.login_data, headers=self.headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["isAddedToDB"], False)
        self.assertEqual(response.json()["reason"], "user exist")

    def test2_login_right_credentials(self):
        global token
        response = requests.post(f"{self.url}/login_user", json=self.login_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("token" in response.json())
        token = response.json()["token"]

    def test3_login_wrong_credentials(self):
        data = {
            "nickname": "test_nickname",
            "password": "wrong_password"
        }
        response = requests.post(f"{self.url}/login_user", json=data, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"isLogged": False})

    def test4_delete_user_by_email(self):
        response = requests.get(f"{self.url}/delete_user_by/{self.login_data['email']}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["is_deleted"], True)

    def test5_delete_user_by_emain(self):
        self.headers['Authorization'] = f'Bearer {token}'
        response = requests.post(f"{self.url}/create_event", json=self.event_data, header=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["msg"], "success")

if __name__ == '__main__':
    unittest()
    app.run(debug=True)