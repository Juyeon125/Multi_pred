import multiprocessing
import os
import subprocess
import sys
import time
from datetime import datetime

from flask import Flask, redirect, escape, render_template, request, session
from flask_mail import Mail, Message

import mysql_dao
from config import Configuration

app = Flask(__name__)

config = Configuration()
config.load_file("./config.json")

app.config['MAIL_SERVER'] = config.mail['host']
app.config['MAIL_PORT'] = config.mail['port']
app.config['MAIL_USERNAME'] = config.mail['user']
app.config['MAIL_PASSWORD'] = config.mail['password']
app.config['MAIL_USE_SSL'] = config.mail['use_ssl']
app.config['MAIL_USE_TLS'] = config.mail['use_tls']
mail = Mail(app)

sys.path.append("/usr/bin/")
sys.path.append("/usr/local/bin/")
sys.path.append("/usr/local/lib/")
sys.path.append("/usr/local/share/EMBOSS/")
sys.path.append("/home/juyeon/Program/Multi_Pred/multi_pred/vendor/DETECTv2/")
sys.path.append("/home/juyeon/Program/Multi_Pred/multi_pred/vendor/blast/bin/")
sys.path.append("/home/juyeon/Program/Multi_Pred/multi_pred/vendor/EMBOSS-6.6.0/nucleus/.libs/")


@app.route('/', methods=['GET'])
def home():
    # Session Check for exist user session info
    # if 'username' in session:
    #     result = '%s' % escape(session['username'])
    #     return render_template('mainFrame.html', loginId=result)
    # else:
    #     session['username'] = ''
    #     result = '%s' % escape(session['username'])
    #     return redirect('/')

    return render_template('index.html')


@app.route("/predict", methods=['GET', 'POST'])
def predict_all():
    start = time.time()  # 시작 시간 저장
    input_seq = ''
    if request.method == "POST":
        input_seq = request.form["seq"]

    manager = multiprocessing.Manager()
    processes = []
    result = manager.dict()

    p1 = multiprocessing.Process(name='DeepEC', target=predict_deepec, args=(input_seq, result,))
    processes.append(p1)
    p2 = multiprocessing.Process(name='ECPred', target=predict_ecpred, args=(input_seq, result,))
    processes.append(p2)
    p3 = multiprocessing.Process(name='DETECT', target=predict_detect, args=(input_seq, result,))
    processes.append(p3)
    p4 = multiprocessing.Process(name='eCAMI', target=predict_ecami, args=(input_seq, result,))
    processes.append(p4)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    # TODO 결과 종합해서 출력, 깃허브
    api_result = {}
    api_result['DeepEC'] = result['DeepEC']
    api_result['ECPred'] = result['ECPred']
    api_result['DETECT'] = result['DETECT']
    api_result['eCAMI'] = result['eCAMI']
    api_result['final_result'] = fun(api_result['DeepEC']['deepec_ec'], api_result['ECPred']['ecpred_ec'],
                                     api_result['DETECT']['detect_ec'], api_result['DeepEC']['deepec_acc'],
                                     api_result['ECPred']['ecpred_acc'], api_result['DETECT']['detect_acc'])
    print("time :", time.time() - start)
    return api_result


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


# @app.route("/predict/algorithm", methods=['GET', 'POST'])
def fun(ec_1, ec_2, ec_3, acc_1, acc_2, acc_3):
    ec_list = []
    acc_list = []
    s_list = []
    re_list = []

    ec_list.append(ec_1)
    ec_list.append(ec_2)
    ec_list.append(ec_3)
    acc_list.append(acc_1)
    acc_list.append(acc_2)
    acc_list.append(acc_3)

    # S값 구하기
    for i in ec_list:
        cnt = ec_list.count(i)
        s_list.append(cnt / 3)

    # R값 구하기
    for i in range(len(ec_list)):
        temp = s_list[i] * acc_list[i]
        re_list.append(temp)

    sum_relist = sum(re_list)
    finre_list = []

    for i in range(len(ec_list)):
        temp = re_list[i] / sum_relist
        finre_list.append(round(temp, 3))

    for v in range(0, len(ec_list)):
        if (v == re_list.index(max(re_list))):
            final_ec = ec_list[v]

    rec_ec = mysql_dao.connect_result(final_ec)

    final_result = {"final_ec": final_ec,
                    "final_name": rec_ec[0], "final_reac": rec_ec[1]}

    return final_result


def predict_detect(input_seq, result):
    timestamp = str(round(datetime.utcnow().timestamp() * 1000))

    input_path = f'/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Input/{timestamp}.fasta'
    with open(input_path, 'w') as file:
        file.write('>Sample\n' + input_seq)

    output_base_path = "/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Output"
    output_default_file_path = f"{output_base_path}/{timestamp}_detect_output.out"

    detect_path = "/home/juyeon/Program/Multi_Pred/multi_pred/vendor/DETECTv2/detect.py"

    subprocess.run(["python", detect_path, input_path,
                    "--output_file", output_default_file_path,
                    "--num_threads", "4"])

    file = open(output_default_file_path, 'r')

    header = next(file)
    detect_ec = None
    detect_acc = 0.0

    try:
        for line in file:
            line = line.strip().split("\t")
            detect_ec = line[1]
            detect_acc = float(line[2])
            break
    except StopIteration:
        detect_ec = None

    if detect_ec is None:
        detect_result_json = {"detect_ec": "Unpredictable", "detect_acc": 0, "detect_name": "", "detect_reac": ""}
    else:
        alpha_info = mysql_dao.connect_result(detect_ec)
        detect_result_json = {"detect_ec": detect_ec, "detect_acc": detect_acc, "detect_name": alpha_info[0],
                              "detect_reac": alpha_info[1]}

    result.update({'DETECT': detect_result_json})


def predict_ecami(input_seq, result):
    timestamp = str(round(datetime.utcnow().timestamp() * 1000))
    ecami_input_path = f'/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Input/{timestamp}.fasta'

    file = open(ecami_input_path, 'w')
    file.write('>Sample\n' + input_seq)
    file.close()

    ecami_path = "/home/juyeon/Program/Multi_Pred/multi_pred/vendor/eCAMI"
    ecami_execute_path = os.path.join(ecami_path, "prediction.py")
    ecami_kmer_db_path = os.path.join(ecami_path, "CAZyme")
    ecami_output_path = os.path.join("/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Output/",
                                     f"{timestamp}_ecami_output.txt")

    subprocess.run(["python3", ecami_execute_path,
                    "-input", ecami_input_path,
                    "-kmer_db", ecami_kmer_db_path,
                    "-output", ecami_output_path])

    file = open(ecami_output_path, 'r')
    s = file.read()
    if s == "":
        ecami_result_json = {"ecami_ec": "Unpredictable", "ecami_name": "", "ecami_reac": ""}
    else:
        s_split = s.split("\t")
        s_double_split = s_split[2].split("|")
        s_result_split = s_double_split[3].split(":")

        ecami_ec = s_result_split[0]

        alpha_info = mysql_dao.connect_result(ecami_ec)

        ecami_result_json = {"ecami_ec": ecami_ec, "ecami_name": alpha_info[0], "ecami_reac": alpha_info[1]}

    file.close()

    result.update({'eCAMI': ecami_result_json})


def predict_ecpred(input_seq, result):
    timestamp = str(round(datetime.utcnow().timestamp() * 1000))
    ecpred_input_path = f'/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Input/{timestamp}.fasta'

    file = open(ecpred_input_path, 'w')
    file.write('>Sample\n' + input_seq)
    file.close()

    ecpred_path = "/home/juyeon/Program/Multi_Pred/multi_pred/vendor/ECPred/"
    ecpred_execute_path = os.path.join(ecpred_path, "ECPred.jar")
    ecpred_output_path = os.path.join("/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Output/",
                                      f"{timestamp}_ecpred_output.tsv")

    subprocess.run(["java", "-jar", ecpred_execute_path,
                    "blast", ecpred_input_path,
                    ecpred_path, "temp/",
                    ecpred_output_path])

    file = open(ecpred_output_path, 'r')
    result_ecpred = file.read()

    result_ecpred_split = result_ecpred.split("\n")
    ec_number_ecpred = result_ecpred_split[1].split("\t")
    ecpred_ec = ec_number_ecpred[1]
    ecpred_acc = float(ec_number_ecpred[2])

    alpha_info = mysql_dao.connect_result(ecpred_ec)

    ecpred_result_json = {"ecpred_ec": ecpred_ec, "ecpred_acc": ecpred_acc, "ecpred_name": alpha_info[0],
                          "ecpred_reac": alpha_info[1]}

    file.close()

    result.update({'ECPred': ecpred_result_json})


def predict_deepec(input_seq, result):
    timestamp = str(round(datetime.utcnow().timestamp() * 1000))
    deepec_input_path = f'/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Input/{timestamp}.fasta'

    file = open(deepec_input_path, 'w')
    file.write('>Sample\n' + input_seq)
    file.close()

    deepec_path = "/home/juyeon/Program/Multi_Pred/multi_pred/vendor/deepec"
    deepec_execute_path = os.path.join(deepec_path, "deepec.py")
    deepec_output_path = os.path.join("/home/juyeon/Program/Multi_Pred/multi_pred/vendor/Output/",
                                      f"{timestamp}_deepec_output")

    subprocess.run(["python3", deepec_execute_path,
                    "-i", deepec_input_path,
                    "-o", deepec_output_path])

    deepec_output_path = os.path.join(deepec_output_path, "log_files", "4digit_EC_prediction.txt")

    file = open(deepec_output_path, 'r')
    s = file.read()
    s_split = s.split("\n")
    s_double_split = s_split[1].split(":")

    if len(s_double_split) < 2:
        deepec_result_json = {"deepec_ec": "UnPredictable", "deepec_acc": "",
                              "deepec_name": "", "deepec_reac": ""}

    else:
        s_triple_split = s_double_split[1].split("\t")
        deepec_ec = s_triple_split[0]
        deepec_acc = float(s_triple_split[1])

        alpha_info = mysql_dao.connect_result(deepec_ec)

        deepec_result_json = {"deepec_ec": deepec_ec, "deepec_acc": deepec_acc, "deepec_name": alpha_info[0],
                              "deepec_reac": alpha_info[1]}

    file.close()

    result.update({'DeepEC': deepec_result_json})


if __name__ == '__main__':
    app.debug = True
    app.use_reloader = True
    app.secret_key = os.urandom(12).hex()
    app.run(debug=True)
