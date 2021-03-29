import os
import subprocess

from app.preprocess import get_deepec_path, get_ecpred_path, get_ecami_path


def predict_deepec(input_sequence, output_path, req_seq_file_path, result):
    deepec_execute_path = get_deepec_path() + "/deepec.py"
    deepec_output_path = os.path.join(output_path, "deepec")
    os.makedirs(deepec_output_path)

    subprocess.call(f"export PATH={get_deepec_path()}/diamond:$PATH;"
                    f"{get_deepec_path()}/venv/bin/python "
                    f"{deepec_execute_path} "
                    f"-i {req_seq_file_path} "
                    f"-o {deepec_output_path}", shell=True)

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

    final_result = {}

    for input_enzyme in input_sequence:
        query_id = input_enzyme['id']

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
            final_result[query_id] = {"result": ec_activity}

        except KeyError:
            final_result[query_id] = {"result": None}
            continue
        except ValueError:
            final_result[query_id] = {"result": None}
            continue

    result.update({'DeepEC': final_result})


def predict_ecpred(input_sequence, output_path, req_seq_file_path, result):
    ecpred_execute_path = get_ecpred_path() + "/ECPred.jar"
    ecpred_output_path = os.path.join(output_path, "ecpred")
    os.makedirs(ecpred_output_path)

    subprocess.run(f"cd {get_ecpred_path()};"
                   f"java -jar {ecpred_execute_path} "
                   f"weighted "
                   f"{req_seq_file_path} "
                   f"{get_ecpred_path()}/ "
                   f"temp/ "
                   f"{ecpred_output_path}/results.tsv", shell=True)

    result.update({'ECPred': None})


def predict_ecami(input_sequence, output_path, req_seq_file_path, result):
    ecami_execute_path = get_ecami_path() + "/prediction.py"
    ecami_output_path = os.path.join(output_path, "ecami")
    os.makedirs(ecami_output_path)

    subprocess.run(f"cd {get_ecami_path()};"
                   f"{get_ecami_path()}/venv/bin/python "
                   f"{ecami_execute_path} "
                   f"-jobs 4 "
                   f"-input {req_seq_file_path} "
                   f"-kmer_db CAZyme "
                   f"-output {ecami_output_path}/result.txt", shell=True)

    result.update({'eCAMI': None})


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
