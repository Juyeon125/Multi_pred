import os
import subprocess
from datetime import datetime

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
        detect_result_json = {"detect_ec": "Unpredictable", "detect_acc": 0.0, "detect_name": "", "detect_reac": ""}
    else:
        detect_result_json = {"detect_ec": detect_ec, "detect_acc": detect_acc}

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

        ecami_result_json = {"ecami_ec": ecami_ec}

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

    ecpred_result_json = {"ecpred_ec": ecpred_ec, "ecpred_acc": ecpred_acc}

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
        deepec_result_json = {"deepec_ec": "UnPredictable", "deepec_acc": 0.0,
                              "deepec_name": "", "deepec_reac": ""}

    else:
        s_triple_split = s_double_split[1].split("\t")
        deepec_ec = s_triple_split[0]
        deepec_acc = float(s_triple_split[1])

        deepec_result_json = {"deepec_ec": deepec_ec, "deepec_acc": deepec_acc}

    file.close()

    result.update({'DeepEC': deepec_result_json})


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
    deepec_result = temp_result['DeepEC']['deepec_ec']
    deepec_pred.append(deepec_result)

    predict_ecpred(seq_list[i], result=temp_result)
    ecpred_result = temp_result['ECPred']['ecpred_ec']
    ecpred_pred.append(ecpred_result)

    predict_detect(seq_list[i], result=temp_result)
    detect_result = temp_result['DETECT']['detect_ec']
    detect_pred.append(detect_result)

    predict_ecami(seq_list[i], result=temp_result)
    ecami_result = temp_result['eCAMI']['ecami_ec']
    ecami_pred.append(ecami_result)

    algorithm_result = fun(temp_result['DeepEC']['deepec_ec'], temp_result['ECPred']['ecpred_ec'],
                           temp_result['DETECT']['detect_ec'], temp_result['DeepEC']['deepec_acc'],
                           temp_result['ECPred']['ecpred_acc'], temp_result['DETECT']['detect_acc'])

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
