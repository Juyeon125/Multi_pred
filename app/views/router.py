from flask import current_app, render_template, session, request

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
        return '{"result":false, "message":"Not found user"}', 400, {'Content-Type': 'application/json; charset=utf-8'}

    if user['password'] != form_data['password']:
        return '{"result":false, "message":"password_error"}', 400, {'Content-Type': 'application/json; charset=utf-8'}

    session['user'] = user

    return '{"result":true}', 200, {'Content-Type': 'application/json; charset=utf-8'}


@a.route('/sign_up', methods=['GET'])
def sign_up():
    if 'user' not in session:
        return render_template('sign_up.html')
    else:
        return redirect("/")


@a.route('/sign_up.do', methods=['POST'])
def sign_up_async():
    form_data = request.data.decode('utf-8')
    form_data = json.loads(form_data)

    result = database.save_user(form_data['name'], form_data['email'], form_data['password'])
    if type(result) is not dict:
        return '{"result":false, "message":"' + result + '"}', 400, {'Content-Type': 'application/json; charset=utf-8'}

    user = result
    session['user'] = user

    return '{"result":true}', 200, {'Content-Type': 'application/json; charset=utf-8'}


@a.route('/enzyme_tree', methods=['GET'])
def enzyme_tree():
    db = current_app.config['DB']
    enzyme_info = db.find_all_enzyme()
    len_data = len(enzyme_info)

    return render_template('enzyme_tree.html', enzyme_info=enzyme_info, len_data=len_data)
