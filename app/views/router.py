import multiprocessing
import os
import time

from Bio import SeqIO
from flask import current_app, render_template, session, request, jsonify, redirect

from app.blueprints import app as a
from app.exec.algorithm import predict_deepec, predict_ecpred, predict_ecami


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
def predict_all():
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

    manager = multiprocessing.Manager()
    processes = []
    result = manager.dict()

    # p1 = multiprocessing.Process(name='DeepEC', target=predict_deepec,
    #                              args=(request_sequence, output_path, request_seq_file_path, result,))
    # processes.append(p1)

    # p2 = multiprocessing.Process(name='ECPred', target=predict_ecpred,
    #                              args=(request_sequence, output_path, request_seq_file_path, result,))
    # processes.append(p2)

    p3 = multiprocessing.Process(name='eCAMI', target=predict_ecami,
                                 args=(request_sequence, output_path, request_seq_file_path, result,))
    processes.append(p3)

    # p4 = multiprocessing.Process(name='eCAMI', target=predict_ecami, args=(input_seq, result,))
    # processes.append(p4)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    # TODO 결과 종합해서 출력, 깃허브
    api_result = {}
    api_result['DeepEC'] = result['DeepEC']
    # api_result['ECPred'] = result['ECPred']
    # api_result['DETECT'] = result['DETECT']
    # api_result['eCAMI'] = result['eCAMI']
    # api_result['final_result'] = fun(api_result['DeepEC']['deepec_ec'], api_result['ECPred']['ecpred_ec'],
    #                                  api_result['DETECT']['detect_ec'], api_result['DeepEC']['deepec_acc'],
    #                                  api_result['ECPred']['ecpred_acc'], api_result['DETECT']['detect_acc'])
    print(api_result)
    return api_result


@a.route("/logout", methods=['GET'])
def logout():
    session.pop('user', None)
    return redirect("/")


@a.route("/test", methods=['GET'])
def test():
    return render_template("test.html")


@a.route("/predict_hist",  methods=['GET'])
def predict_hist():
    db = current_app.config['DB']
    history_info = db.find_all_history()
    len_data = len(history_info)

    return render_template('predict_hist.html', history_info=history_info, len_data=len_data)