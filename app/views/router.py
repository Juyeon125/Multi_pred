from flask import current_app, render_template, session, request, jsonify

from app.blueprints import app as a


@a.context_processor
def load_logged_in_user():
    if 'user' in session:
        user = session['user']
    else:
        user = None

    return dict(user=user)


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
