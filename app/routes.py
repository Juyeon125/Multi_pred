from flask import Flask, url_for, session, redirect, escape, render_template, request, session
import mysql_dao
import json
from io import StringIO
import numpy as np
import pandas as pd
import flask
import smtplib
import subprocess
from flask_mail import Mail, Message
import os

app = Flask(__name__)

input_path = "./config.json"

with open(input_path, "r") as json_file:
    data = json.load(json_file)

app.config['MAIL_SERVER'] = data['mailServer']
app.config['MAIL_PORT'] = data['mailPort']
app.config['MAIL_USERNAME'] = data['usernameConfig']
app.config['MAIL_PASSWORD'] = data['passwordConfig']
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
mail = Mail(app)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


@app.route('/')
def index():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('mainFrame.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
        return redirect('/')


@app.route('/search_page')
def search_page():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('search.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
        return redirect('/search_page')


@app.route('/intro_page')
def intro_page():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('intro_page.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
        return redirect('/intro_page')


@app.route('/developer_page')
def developer_page():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('developer_page.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
    return redirect('/developer_page')


@app.route('/contact_page')
def contact_page():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('contact_page.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
    return redirect('/contact_page')


@app.route('/register_page')
def register_page():
    return render_template('register_page.html')


@app.route('/login_page')
def login_page():
    return render_template('login_page.html')


@app.route('/mypage')
def mypage():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        content = mysql_dao.get_saveInfo_Select(result)
        return render_template('mypage.html', loginId=result, content=content)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
    return redirect('/')


@app.route('/forgot_password_page')
def forgot_password_page():
    return render_template('forgot_password_page.html')


@app.route('/ecFunction_page')
def ecFunction_page():
    content = mysql_dao.get_tableSelect()
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('ec_function.html', loginId=result, content=content)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
    return redirect('/ecFunction_page')


@app.route("/login_route", methods=['GET', 'POST'])
def login_route():
    if request.method == "POST":
        reqid = request.form["id"]
        reqpw = request.form["pw"]
        content = mysql_dao.get_dbSelect_login(reqid, reqpw)
        if (content != 'fail'):
            result = content["email"]
            session['username'] = result
        else:
            result = "fail"
    return result


@app.route("/password_route", methods=['GET', 'POST'])
def password_route():
    if request.method == "POST":
        reqid = request.form["id"]
        reqname = request.form["name"]
        content = mysql_dao.get_dbSelect_password(reqid, reqname)
    return content


@app.route("/logout")
def logout_route():
    session.pop('username', None)
    return redirect(request.args.get('url'))


@app.route('/register_route', methods=['GET', 'POST'])
def register_route():
    if request.method == "POST":
        reqid = request.form["id"]
        reqpw = request.form["pw"]
        reqfi = request.form["first"]
        reqla = request.form["last"]
        content = mysql_dao.get_dbInsert_register(reqid, reqpw, reqfi, reqla)
    else:
        content = ''

    return content


@app.route("/contact_page", methods=['post', 'get'])
def email_test():
    if request.method == 'POST':
        senders = request.form['name_sender']
        senders2 = request.form['email_sender']
        receiver = request.form['email_receiver']
        content = '보내는 사람:' + senders + '\n' + '답장 받을 이메일:' + senders2 + '\n' + '내용:' + request.form['email_content']
        receiver = receiver.split(',')

        for i in range(len(receiver)):
            receiver[i] = receiver[i].strip()

        result = send_email(senders, receiver, content)

        if result == 'success':
            return render_template('contact_page.html', content="Email is sent")
        else:
            return render_template('contact_page.html', content="Email is not sent")
    else:
        return render_template('contact_page.html')


def send_email(senders, receiver, content):
    msg = Message('SAMPLE 문의 메일', sender=senders, recipients=receiver)
    msg.body = content
    mail.send(msg)

    return 'success'


@app.route('/test')
def test():
    ecami_path = "/home/juyeon/Program/Multi_Pred/multi_pred/app/eCAMI"  # python prediction.py
    execute_path = os.path.join(ecami_path, "prediction.py")
    input_path = os.path.join(ecami_path, "examples/prediction/input/test.faa")
    kmer_db_path = os.path.join(ecami_path, "CAZyme")
    output_path = os.path.join(ecami_path, "examples/prediction/output/new-output.txt")

    subprocess.run(["python", execute_path,
                    "-input", input_path,
                    "-kmer_db", kmer_db_path,
                    "-output", output_path])

    return render_template('test.html')


if __name__ == '__main__':
    app.debug = True
    app.use_reloader = True
    app.secret_key = "123123123"
    app.run(debug=True)
