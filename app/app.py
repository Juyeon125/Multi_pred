import json
import multiprocessing
import os
import platform
import subprocess
import sys
import time
from datetime import datetime

import git
from Bio import SeqIO
from flask import Flask, redirect, escape, render_template, request, session
from flask_mail import Message
from tqdm import tqdm

import mysql_dao
import requests
from config import Configuration
from connection import Database

app = Flask(__name__)

config = Configuration()
config.load_file("./config.json")

database = Database(config.mysql['host'], config.mysql['user'], config.mysql['password'], config.mysql['database'])


def get_requests_path():
    cur_path = os.path.abspath(os.path.curdir)
    requests_path = os.path.join(cur_path, "requests")

    if not os.path.exists(requests_path):
        os.makedirs(requests_path)

    return requests_path


def get_vendor_path():
    cur_path = os.path.abspath(os.path.curdir)
    vendor_path = os.path.join(cur_path, "vendor")

    if not os.path.exists(vendor_path):
        os.makedirs(vendor_path)

    return vendor_path


def get_deepec_path():
    vendor_path = get_vendor_path()
    deepec_path = os.path.join(vendor_path, "deepec")
    return deepec_path


def preprocess_deepec():
    vendor_path = get_vendor_path()

    # region [ DeepEC Program Check ]
    print("Check DeepEC Program...")
    deepec_path = os.path.join(vendor_path, "deepec")
    if not os.path.exists(deepec_path):
        # Cloning DeepEC Program from bitbucket
        print("Download DeepEC Program... ", end="")
        git.Git(vendor_path).clone("https://bitbucket.org/kaistsystemsbiology/deepec.git")
        print("Done!")
    # endregion

    # region [ Diamond Program Check ]
    print("Check Diamond Program...")
    diamond_path = os.path.join(deepec_path, "diamond")

    if platform.system() == "Linux":
        file_name = "/diamond"
    elif platform.system() == "Windows":
        file_name = "/diamond.exe"
    else:
        raise OSError("Unsupported OS")

    if not os.path.exists(diamond_path + file_name):
        if not os.path.exists(diamond_path):
            os.makedirs(diamond_path)

        # Download Diamond Program from github
        print("Download Diamond Program...", end="")

        if platform.system() == "Linux":
            diamond_url = "https://download.sharenshare.kr/allec/diamond-linux64.tar.gz"
            compressed_file_name = "diamond-linux64.tar.gz"
        elif platform.system() == "Windows":
            diamond_url = "https://download.sharenshare.kr/allec/diamond-windows.zip"
            compressed_file_name = "diamond-windows.zip"
        else:
            raise OSError("Unsupported OS")

        response = requests.get(diamond_url, stream=True)
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024
        progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
        with open(diamond_path + "/" + compressed_file_name, "wb") as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            raise OSError("Diamond download error")

        # Decompress Diamond Program
        if platform.system() == "Linux":
            subprocess.run(f"tar -xvzf {diamond_path + '/' + compressed_file_name}", shell=True)
        elif platform.system() == "Windows":
            import zipfile
            diamond_zip = zipfile.ZipFile(diamond_path + "/" + compressed_file_name)
            diamond_zip.extractall(diamond_path)
            diamond_zip.close()
        else:
            raise OSError("Unsupported OS")

        os.remove(diamond_path + "/" + compressed_file_name)
    sys.path.append(diamond_path)
    # endregion

    # region [ DeepEC Python Venv Check ]
    print("Check DeepEC Venv...")
    if not os.path.exists(f"{deepec_path}/venv"):
        # Create venv
        subprocess.call(f"{sys.executable} -m venv {deepec_path}/venv", shell=True)
        venv_python_path = deepec_path + "/venv/bin/" + "python" if platform.system() == "Linux" else "python.exe"

        # Update pip
        subprocess.call(f"{venv_python_path} -m pip install -U pip", shell=True)

        # Install DeepEC dependencies
        dependencies = set()
        dependencies.add("tensorflow==1.5.0")
        dependencies.add("numpy==1.16.2")
        dependencies.add("biopython==1.78")
        dependencies.add("h5py==2.7.1")
        dependencies.add("keras==2.1.6")
        dependencies.add("markdown==2.6.11")
        dependencies.add("mock==2.0.0")
        dependencies.add("pandas==0.19.2")
        dependencies.add("scikit-learn==0.19.0")
        dependencies.add("scipy==1.1.0")

        subprocess.call(f"{venv_python_path} -m pip install {' '.join(dependencies)}", shell=True)
    # endregion

    print(f"DeepEC Path: {deepec_path}")
    print(f"Diamond Path: {diamond_path}")


def preprocess_ecpred():
    print("Check ECPred Program...")
    print("Not implemented")


def preprocess_ecami():
    print("Check eCAMI Program...")
    print("Not implemented")


def preprocess_detectv2():
    print("Check DETECTv2 Program...")
    print("Not implemented")


def predict_deepec(output_path, req_seq_file_path, result):
    deepec_execute_path = get_deepec_path() + "/deepec.py"
    deepec_output_path = os.path.join(output_path, "deepec")
    os.makedirs(deepec_output_path)

    subprocess.run([f"{get_deepec_path()}/venv/bin/{'python' if platform.system() == 'Linux' else 'python.exe'}",
                    deepec_execute_path,
                    "-i", req_seq_file_path,
                    "-o", deepec_output_path], shell=True)

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


@app.route("/predict", methods=['POST'])
def predict_all():
    form_data = request.data.decode('utf-8')
    form_data = json.loads(form_data)

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

    manager = multiprocessing.Manager()
    processes = []
    result = manager.dict()

    p1 = multiprocessing.Process(name='DeepEC', target=predict_deepec,
                                 args=(output_path, request_seq_file_path, result,))
    processes.append(p1)
    # p2 = multiprocessing.Process(name='ECPred', target=predict_ecpred, args=(input_seq, result,))
    # processes.append(p2)
    # p3 = multiprocessing.Process(name='DETECT', target=predict_detect, args=(input_seq, result,))
    # processes.append(p3)
    # p4 = multiprocessing.Process(name='eCAMI', target=predict_ecami, args=(input_seq, result,))
    # processes.append(p4)

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


@app.route('/introduction')
def introduction():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('introduction.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
        return redirect('/introduction')


@app.route('/about_us')
def about_us():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('about_us.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
    return redirect('/about_us')


@app.route('/contact_page')
def contact_page():
    if 'username' in session:
        result = '%s' % escape(session['username'])
        return render_template('contact_page.html', loginId=result)
    else:
        session['username'] = ''
        result = '%s' % escape(session['username'])
    return redirect('/contact_page')


@app.route('/sign_in', methods=['GET'])
def sign_in():
    return render_template('sign_in.html')


@app.route("/sign_in", methods=['POST'])
def sign_in_async():
    form_data = request.data.decode('utf-8')
    form_data = json.loads(form_data)

    user = database.find_by_user_email(form_data['email'])

    if user is None:
        return '{"result":false, "message":"Not found user"}', 400, {'Content-Type': 'application/json; charset=utf-8'}

    if user['password'] != form_data['password']:
        return '{"result":false, "message":"password_error"}', 400, {'Content-Type': 'application/json; charset=utf-8'}

    return '{"result":true}', 200, {'Content-Type': 'application/json; charset=utf-8'}


@app.route('/sign_up', methods=['GET'])
def sign_up():
    return render_template('sign_up.html')


@app.route('/sign_up', methods=['POST'])
def sign_up_async():
    form_data = request.data.decode('utf-8')
    form_data = json.loads(form_data)

    result = database.sign_up_user(form_data['name'], form_data['email'], form_data['password'])
    if type(result) is not dict:
        return '{"result":false, "message":"' + result + '"}', 400, {'Content-Type': 'application/json; charset=utf-8'}

    user = result
    # TODO 세션에 로그인 정보를 저장

    return '{"result":true}', 200, {'Content-Type': 'application/json; charset=utf-8'}


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


@app.route('/find_account')
def find_account():
    return render_template('find_account.html')


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


if __name__ == '__main__':
    preprocess_deepec()
    preprocess_ecpred()
    preprocess_ecami()
    preprocess_detectv2()

    app.debug = True
    app.use_reloader = True
    app.secret_key = os.urandom(12).hex()
    app.run(debug=True)
