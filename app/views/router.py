import multiprocessing
import os
import time

from Bio import SeqIO
from flask import Flask, current_app, render_template, session, request, jsonify, redirect

from app.blueprints import app as a
from app.exec.algorithm import predict_all_methods
from app.extensions.extension import NotFoundError, BadRequestError

import smtplib
from email.mime.text import MIMEText

@a.context_processor
def load_logged_in_user():
    if 'user' in session:
        user = session['user']
    else:
        user = None

    return dict(user=user)


def get_requests_path():
    cur_path = os.path.abspath(os.path.curdir)
    requests_path = os.path.join(cur_path, "requests")

    if not os.path.exists(requests_path):
        os.makedirs(requests_path)

    return requests_path


@a.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@a.route('/introduction', methods=['GET'])
def introduction():
    return render_template('introduction.html')


@a.route('/contact', methods=['GET'])
def contact():
    return render_template('contact_page.html')


def sendMail(name, sender, receiver, msg):
    smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtp.login(receiver, 'ftuvxkgxifbejote')
    msg = MIMEText(msg)
    msg['Subject'] = name + '의 All EC 문의메일'
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

@a.route("/contact.do", methods=['POST'])
def contact_async():
    form_data = request.get_json()

    sendMail(form_data['user_name'], form_data['user_email'], 'juyeone125@gmail.com', form_data['mail_content'])

    return jsonify({'result': True}), 200


@a.route('/about_us', methods=['GET'])
def about_us():
    return render_template('about_us.html')


@a.route('/sign_in', methods=['GET'])
def sign_in():
    if 'user' not in session:
        return render_template('sign_in.html')
    else:
        return redirect("/")


@a.route("/sign_in.do", methods=['POST'])
def sign_in_async():
    form_data = request.get_json()
    db = current_app.config['DB']
    user = db.find_user_by_user_email(form_data['email'])

    if user is None:
        return jsonify({'result': False, 'message': 'not found user'}), 400

    if user['password'] != form_data['password']:
        return jsonify({'result': False, 'message': 'password error'}), 400

    session['user'] = user

    return jsonify({'result': True}), 200


@a.route('/sign_up', methods=['GET'])
def sign_up():
    if 'user' not in session:
        return render_template('sign_up.html')
    else:
        return redirect("/")


@a.route('/sign_up.do', methods=['POST'])
def sign_up_async():
    form_data = request.get_json()
    db = current_app.config['DB']

    result = db.save_user(form_data['name'], form_data['email'], form_data['password'])
    if type(result) is not dict:
        return jsonify({'result': False, 'message': result}), 400

    session['user'] = result

    return jsonify({'result': True}), 200


@a.route('/enzyme_tree', methods=['GET'])
def enzyme_tree():
    db = current_app.config['DB']
    enzyme_info = db.find_all_enzyme()
    len_data = len(enzyme_info)

    return render_template('enzyme_tree.html', enzyme_info=enzyme_info, len_data=len_data)


@a.route("/predict.do", methods=['POST'])
def predict_all_async():
    form_data = request.get_json()

    request_folder_path = get_requests_path()
    timestamp = str(int(time.time() * 10000000))

    output_path = os.path.join(request_folder_path, timestamp)
    os.makedirs(output_path)

    request_seq_file_path = os.path.join(output_path + "/request_seq.fasta")
    with open(request_seq_file_path, 'w+') as request_seq_file:
        form_data['sequence_text'] = form_data['sequence_text'].replace("\r\n", "\n")
        request_seq_file.write(form_data['sequence_text'])

    request_sequence = []

    for record in SeqIO.parse(request_seq_file_path, "fasta"):
        request_sequence.append({
            'id': record.id,
            'name': record.name,
            'description': record.description,
            'sequence': str(record.seq)
        })

    if len(request_sequence) == 0:
        return '{"result":false, "message":"Can not read sequence data"}', 400, {
            'Content-Type': 'application/json; charset=utf-8'}

    job = {
        "idx": timestamp,
        "user_idx": session['user']['user_idx'] if 'user' in session.keys() else None,
        "req_sequences": form_data['sequence_text']
    }

    db = current_app.config['DB']
    job = db.save_job(job)

    job_process = multiprocessing.Process(name=job['idx'], target=predict_all_methods,
                                          args=(job, request_sequence, output_path, request_seq_file_path,))
    job_process.start()

    return job


@a.route("/logout", methods=['GET'])
def logout():
    session.pop('user', None)
    return redirect("/")


@a.route("/user_predict", methods=['GET'])
def user_predict():
    return render_template("user_predict.html")


@a.route("/user_predict.do", methods=['GET'])
def user_predict_async():
    db = current_app.config['DB']

    if 'user' in session:
        user = session['user']
    else:
        user = None

    if user is None:
        raise BadRequestError(code=403, message="Should be sign in!")

    return db.find_predicted_list(user['user_idx'])


@a.route("/predict_hist", methods=['GET'])
def predict_hist():
    db = current_app.config['DB']
    job_idx = request.args.get('job_idx')

    job = db.find_job_by_idx(job_idx)
    if job is None:
        raise NotFoundError(message="Didn't find Job ID!")

    return render_template('predict_hist.html', job_idx=job_idx, job=job)


@a.route("/predict_hist.do", methods=['GET'])
def predict_history_async():
    db = current_app.config['DB']
    job_idx = request.args.get('job_idx')

    job = db.find_job_by_idx(job_idx)
    if job is None:
        raise NotFoundError(message="Didn't find Job ID!")

    job_results = db.find_job_results_by_job_idx(job.idx)
    return job_results


@a.route("/predict_show_log.do", methods=['GET'])
def predict_show_log():
    db = current_app.config['DB']
    job_idx = request.args.get('job_idx')

    job = db.find_job_by_idx(job_idx)
    if job is None:
        raise NotFoundError(message="Didn't find Job ID!")

    methods = ['DeepEC', 'ECPred', 'DETECTv2', 'eCAMI']
    method = request.args.get('method')
    if method not in methods:
        raise BadRequestError(message=f"Can't support method: [{method}]")

    log_path = os.path.join(get_requests_path(), job.idx, method, f"{method}.log")
    if not os.path.exists(log_path):
        return {"result": False}

    with open(log_path, 'r') as f:
        log_content = f.readlines()
        log_content = "".join(log_content)

    return {"result": True, "data": log_content}
