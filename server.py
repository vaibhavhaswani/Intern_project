from flask import Flask, render_template, request
import csv, os, sys
import smtplib
from pathlib import Path
from email.message import EmailMessage
from string import Template
import time

app = Flask(__name__)
t1 = int(time.time())                           #taking the time at which server starts
client_email = "client@website.com"       #client email to share results
admin_mail = "admin@website.com"     #admin mail id
admin_pass = "admin_email_password"                      #admin mail pass
duration = 2592000                          #competition expiry duration in seconds (for 30 days its - 2592000)


'''Index page Routing'''

@app.route('/')
@app.route('/home')
def home():
    t2 = int(time.time())
    if (t2 - t1 >= duration):                     #close the server and declare result if up time duration of server is equal to or more than client specified duration
        result()
        shutdown_server()
    return render_template('index.html')


'''Signup/login forms routing'''

@app.route('/form/<uname>')
@app.route('/form', defaults={'uname': None})
def form(uname):
    t2 = int(time.time())
    if (t2 - t1 >= duration):
        result()
        shutdown_server()
    return render_template("form.html", name=uname)


@app.route('/form2')
def form2():
    t2 = int(time.time())
    if (t2 - t1 >= duration):
        result()
        shutdown_server()
    return render_template('login.html')

'''SignUP/Login methods routing
these routings cover calling of functions for-
    >signup Database entries
    >sending mails to user
    >generating sharable links
    >checking if username already exist
    >validating user login
    >directing to dashboard after successful signup/login
'''


@app.route('/signup', defaults={'uname': None}, methods=['POST', 'GET'])
@app.route('/signup/<uname>', methods=['POST', 'GET'])
def signup(uname):
    if request.method == 'POST':
        data = request.form.to_dict()
        flag = check_user(data['uname'])
        if flag is not None:
            return flag
        data['point'] = 1
        database(data)
        email_user(data['fname'], data['email'], f"http://127.0.0.1:5000/form/{data['uname']}")       #change the host name if required
        if uname is not None:
            res = point_up(uname)
            if res is not None:
                return res
        return render_template("dash.html", points=data['point'], link=f"http://127.0.0.1:5000/form/{data['uname']}")
    else:
        return "<html><body><center><h2>Trouble Signing you up</h2></center></body></html>"


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        uname = request.form.get('uname')
        with open('database.csv', newline='') as csvf:
            db = csv.DictReader(csvf)
            for row in db:
                if row['uname'] == uname:
                    return render_template('dash.html', points=row['point'],
                                           link=f"http://127.0.0.1:5000/form/{row['uname']}")
            return "<html><body><center><h2>User not found</h2></center></body></html>"

    else:
        return "<html><body><center><h2>Trouble loging you in</h2></center></body></html>"


'''Functions for backend'''


#database function to append new entries in database

def database(data):
    with open('database.csv', 'a', newline='') as csvf:
        fields = ['fname', 'lname', 'uname', 'phone', 'email', 'point']
        db = csv.DictWriter(csvf, fields)
        if os.path.getsize('database.csv') == 0:
            db.writeheader()
        db.writerow(data)

#Point increaser function to increase point of a user after successful referral signup

def point_up(name):
    try:
        with open('database.csv', 'r', newline='') as csvf, open('temp.csv', 'w', newline='') as csvw:
            db = csv.DictReader(csvf)
            fields = ['fname', 'lname', 'uname', 'phone', 'email', 'point']
            dbw = csv.DictWriter(csvw, fields)
            dbw.writeheader()
            for rows in db:
                row = rows
                if row['uname'] == name:
                    row['point'] = int(row['point']) + 1
                dbw.writerow(row)
        os.remove('database.csv')
        os.rename('temp.csv', 'database.csv')
    except:
        return "<html><body><center><h2>Server Database error</h2></center></body></html>"


#function to check if username already exist
def check_user(uname):
    with open('database.csv', newline='') as csvf:
        db = csv.DictReader(csvf)
        for row in db:
            if row['uname'] == uname:
                return "<html><body><center><h2>Username Already Exist</h2>try using different username</center></body></html>"


#function to send registration email to user after successful signup
def email_user(name, id, ulink):
    body = Template(Path('templates/email.html').read_text())
    email = EmailMessage()
    email['From'] = "HoneyMint Talcum"
    email['to'] = id
    email['Subject'] = "Thanks For Registration"
    email.set_content(body.substitute({'user': name, 'link': ulink}), 'html')
    try:
        with smtplib.SMTP('smtp.gmail.com', port=587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(admin_mail, admin_pass)
            smtp.send_message(email)
    except:
        print("Smtp login Error:Review email settings")

#function to shutdown server after competion closes
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


#function to sort the database according to points
def sortdata(data):
    return sorted(list(data), key=lambda k: k['point'], reverse=True)


#function to send final results to client
def result():
    body = Template("<html><body><center><h1>Winner Is: $name</h1><h4>username:$user</h4><br><br>Points earned:$points</center></body></html>")
    with open('database.csv', newline='') as csvf:
        db = csv.DictReader(csvf)
        winner = sortdata(db)[0]
    email = EmailMessage()
    email['From'] = "HoneyMint Talcum"
    email['to'] = client_email
    email['Subject'] = "HoneyMint Result Out"
    email.set_content(
        body.substitute({'name':winner['fname']+" "+winner['lname'],'user':winner['uname'], 'points': winner['point']}),'html')
    with smtplib.SMTP('smtp.gmail.com', port=587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(admin_mail, admin_pass)
        smtp.send_message(email)


if __name__ == '__main__':
    app.run()




'''Developer- Vaibhav Haswani'''