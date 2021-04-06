import json
import multiprocessing
import os
import platform
import subprocess
import sys
import time
from datetime import datetime

import requests
from Bio import SeqIO
from flask import Flask, redirect, escape, render_template, request, session
from flask_mail import Message
from tqdm import tqdm

import mysql_dao
from config import Configuration
from database import Database

app = Flask(__name__)

config = Configuration()
config.load_file("./config.json")

database = Database(config.mysql['host'], config.mysql['user'], config.mysql['password'], config.mysql['database'])








@app.route("/predict.do", methods=['POST'])
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

    # D값 구하기
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
