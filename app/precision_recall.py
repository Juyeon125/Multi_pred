import os
import subprocess
from flask import current_app

from app.preprocess import get_deepec_path, get_ecpred_path, get_ecami_path, get_detect_v2_path

import pandas as pd
from sklearn.metrics import precision_score, recall_score


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

    final_result = {"final_ec": final_ec}

    return final_result


def predict_deepec(input_enzymes, output_path, req_seq_file_path, result):
    deepec_execute_path = get_deepec_path() + "/deepec.py"
    deepec_output_path = os.path.join(output_path, "DeepEC")
    os.makedirs(deepec_output_path)

    # Execute DeepEC
    deepec_log_path = f"{deepec_output_path}/DeepEC.log"
    deepec_log_file = open(deepec_log_path, "w+")
    subprocess.call(f"export PATH={get_deepec_path()}/diamond:$PATH;"
                    f"{get_deepec_path()}/venv/bin/python "
                    f"{deepec_execute_path} "
                    f"-i {req_seq_file_path} "
                    f"-o {deepec_output_path}", shell=True, stdout=deepec_log_file, stderr=subprocess.STDOUT)
    deepec_log_file.close()

    # Get Digit3 Result
    digit3_path = os.path.join(deepec_output_path, "log_files", "3digit_EC_prediction.txt")
    digit3_result = {}
    with open(digit3_path, 'r') as file:
        header = next(file)
        for res in file:
            res = res.strip().split('\t')
            query_id = res[0]
            predicted_ec = res[1]

            if predicted_ec != "EC number not predicted":
                digit3_result[query_id] = {"EC": predicted_ec[3:], "ACTIVITY": float(res[2])}
            else:
                digit3_result[query_id] = {"EC": None, "ACTIVITY": 0.0}

    # Get Digit4 Result
    digit4_path = os.path.join(deepec_output_path, "log_files", "4digit_EC_prediction.txt")
    digit4_result = {}
    with open(digit4_path, 'r') as file:
        header = next(file)
        for res in file:
            res = res.strip().split('\t')
            query_id = res[0]
            predicted_ec = res[1]

            if predicted_ec != "EC number not predicted":
                digit4_result[query_id] = {"EC": predicted_ec[3:], "ACTIVITY": float(res[2])}
            else:
                digit4_result[query_id] = {"EC": None, "ACTIVITY": 0.0}

    # Process Final Result
    final_result = {}

    for enzyme in input_enzymes:
        query_id = enzyme['id']

        try:
            digit3 = digit3_result[query_id]
            digit4 = digit4_result[query_id]

            digit3_ec = digit3['EC']
            digit4_ec = digit4['EC']

            if digit3_ec is None or digit4_ec is None:
                raise ValueError()

            if digit3_ec != '.'.join(digit4_ec.split('.')[:3]):
                raise ValueError()

            ec_activity = digit3['ACTIVITY'] * digit4['ACTIVITY']
            ec_number = digit4_ec

            final_result[query_id] = {"EC": ec_number, "ACTIVITY": ec_activity}
        except KeyError:
            final_result[query_id] = {"EC": None, "ACTIVITY": 0.0}
        except ValueError:
            final_result[query_id] = {"EC": None, "ACTIVITY": 0.0}

        job_result = {
            "ec_number": final_result[query_id]['EC'],
            "accuracy": final_result[query_id]['ACTIVITY']
        }

    result.update({'DeepEC': final_result})


def predict_ecpred(input_enzymes, output_path, req_seq_file_path, result):
    ecpred_execute_path = get_ecpred_path() + "/ECPred.jar"
    ecpred_output_path = os.path.join(output_path, "ECPred")
    os.makedirs(ecpred_output_path)

    # Execute ECPred
    ecpred_log_path = f"{ecpred_output_path}/ECPred.log"
    ecpred_log_file = open(ecpred_log_path, "w+")
    subprocess.run(f"cd {get_ecpred_path()};"
                   f"java -jar {ecpred_execute_path} "
                   f"weighted "
                   f"{req_seq_file_path} "
                   f"{get_ecpred_path()}/ "
                   f"temp/ "
                   f"{ecpred_output_path}/results.tsv", shell=True, stdout=ecpred_log_file, stderr=subprocess.STDOUT)
    ecpred_log_file.close()

    # Get Result
    ecpred_result = {}
    with open(ecpred_output_path + "/results.tsv", "r") as f:
        header = next(f)
        for line in f:
            line = line.strip().split('\t')

            query_id = line[0].split()[0]
            predicted_ec = line[1]
            activity = float(line[2])

            ecpred_result[query_id] = {"EC": predicted_ec, "ACTIVITY": activity}
    for enzyme in input_enzymes:
        query_id = enzyme['id']
        if query_id not in ecpred_result:
            ecpred_result[query_id] = {"EC": None, "ACTIVITY": 0.0}

        job_result = {
            "ec_number": ecpred_result[query_id]['EC'],
            "accuracy": ecpred_result[query_id]['ACTIVITY']
        }

    result.update({'ECPred': ecpred_result})


def predict_ecami(input_enzymes, output_path, req_seq_file_path, result):
    ecami_execute_path = get_ecami_path() + "/prediction.py"
    ecami_output_path = os.path.join(output_path, "eCAMI")
    os.makedirs(ecami_output_path)

    # Execute eCAMI
    ecami_log_path = f"{ecami_output_path}/eCAMI.log"
    ecami_log_file = open(ecami_log_path, "w+")
    subprocess.run(f"cd {get_ecami_path()};"
                   f"{get_ecami_path()}/venv/bin/python "
                   f"{ecami_execute_path} "
                   f"-jobs 4 "
                   f"-input {req_seq_file_path} "
                   f"-kmer_db CAZyme "
                   f"-output {ecami_output_path}/result.txt",
                   shell=True, stdout=ecami_log_file, stderr=subprocess.STDOUT)
    ecami_log_file.close()

    # Get Result
    ecami_result = {}

    for enzyme in input_enzymes:
        query_id = enzyme['id']

        if query_id not in ecami_result:
            ecami_result[query_id] = {"EC": None, "ACTIVITY": 0.0}

        job_result = {
            "ec_number": ecami_result[query_id]['EC'],
            "accuracy": ecami_result[query_id]['ACTIVITY']
        }

        current_app.config['DB'].save_job_result(job_result)

    result.update({'eCAMI': ecami_result})


def predict_detect_v2(input_enzymes, output_path, req_seq_file_path, result):
    detect_v2_execute_path = get_detect_v2_path() + "/detect.py"
    detect_v2_output_path = os.path.join(output_path, "DETECTv2")
    os.makedirs(detect_v2_output_path)

    # Execute DETECTv2
    detect_v2_log_path = f"{detect_v2_output_path}/DETECTv2.log"
    detect_v2_log_file = open(detect_v2_log_path, "w+")
    subprocess.run(f"export PATH="
                   f"{get_ecpred_path()}/lib/ncbi-blast-2.7.1+/bin:"
                   f"{get_ecpred_path()}/lib/EMBOSS-6.5.7/emboss:$PATH;"
                   f"{get_detect_v2_path()}/venv/bin/python "
                   f"{detect_v2_execute_path} "
                   f"{req_seq_file_path} "
                   f"--output_file {detect_v2_output_path}/result.out "
                   f"--top_predictions_file {detect_v2_output_path}/result.top "
                   f"--fbeta_file {detect_v2_output_path}/result.f1 "
                   f"--num_threads {os.cpu_count()} "
                   f"--verbose "
                   f"--beta 1", shell=True, stdout=detect_v2_log_file, stderr=subprocess.STDOUT)

    detect_v2_log_file.close()

    # Get Result
    detect_v2_result = {}
    with open(detect_v2_output_path + "/result.out", 'r') as f:
        header = next(f)
        for line in f:
            line = line.strip().split('\t')

            query_id = line[0]
            predicted_ec = line[1]
            activity = float(line[2])

            detect_v2_result[query_id] = {"EC": predicted_ec, "ACTIVITY": activity}
    for enzyme in input_enzymes:
        query_id = enzyme['id']
        if query_id not in detect_v2_result:
            detect_v2_result[query_id] = {"EC": None, "ACTIVITY": 0.0}

        job_result = {
            "ec_number": detect_v2_result[query_id]['EC'],
            "accuracy": detect_v2_result[query_id]['ACTIVITY']
        }

    result.update({'DETECTv2': detect_v2_result})


seq_list = []
y_true = []
deepec_pred = []
ecpred_pred = []
detect_pred = []
ecami_pred = []
algorithm_pred = []
temp_result = {}

data = pd.read_csv(r"EC number database_Archaea1.csv")

# seq 긁기
for i in data.SEQ[20:40]:
    seq_list.append(i)

# EC number 정답 긁기
for i in data.EC[20:40]:
    y_true.append(i)

for i in range(len(data.SEQ[20:40])):
    predict_deepec(seq_list[i], result=temp_result)
    deepec_result = temp_result['DeepEC']['ec_number']
    deepec_pred.append(deepec_result)

    predict_ecpred(seq_list[i], result=temp_result)
    ecpred_result = temp_result['ECPred']['ec_number']
    ecpred_pred.append(ecpred_result)

    predict_detect_v2(seq_list[i], result=temp_result)
    detect_result = temp_result['DETECT']['ec_number']
    detect_pred.append(detect_result)

    predict_ecami(seq_list[i], result=temp_result)
    ecami_result = temp_result['eCAMI']['ec_number']
    ecami_pred.append(ecami_result)

    algorithm_result = fun(temp_result['DeepEC']['ec_number'], temp_result['ECPred']['accuracy'],
                           temp_result['DETECT']['ec_number'], temp_result['DeepEC']['accuracy'],
                           temp_result['ECPred']['ec_number'], temp_result['DETECT']['accuracy'])

    algorithm_pred.append(algorithm_result["final_ec"])

print(precision_score(y_true, deepec_pred, average='micro'), "DeepEC Precision")
print(recall_score(y_true, deepec_pred, average='micro'), "DeepEC Recall")

print(precision_score(y_true, ecpred_pred, average='micro'), "ECPred Precision")
print(recall_score(y_true, ecpred_pred, average='micro'), "ECPred Recall")

print(precision_score(y_true, detect_pred, average='micro'), "DETECT Precision")
print(recall_score(y_true, detect_pred, average='micro'), "DETECT Recall")

print(precision_score(y_true, ecami_pred, average='micro'), "eCAMI Precision")
print(recall_score(y_true, ecami_pred, average='micro'), "eCAMI Recall")

print(precision_score(y_true, algorithm_pred, average='micro'), "Algorithm Precision")
print(recall_score(y_true, algorithm_pred, average='micro'), "Algorithm Recall")
