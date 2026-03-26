from flask import Flask, g, render_template, request
from flask import jsonify
import sqlite3
import random
from werkzeug.security import check_password_hash, generate_password_hash

DATABASE = 'ducks.db'
answers_list = []
questions_list = []

# initialise app
app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def count_questions(setting_id) -> int:
    sql = """SELECT COUNT(question_id) 
            FROM questions_bridge
            WHERE setting_id = """ + str(setting_id) + ";"  # Count the number of questions for the selected setting
    result = query_db(sql)
    result = result[0]
    result = int(result[0])
    return result

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def home():
    # Home page
    return render_template("homepage.html")

@app.route('/admin_login')
def admin_login():
    return render_template("login.html")

@app.route('/admin_view')
def admin_view():
    return render_template("admin.html")
                        
@app.route('/setting_select')
def setting_select():
    # Presents list of settings to choose from
    # Random option also available
    sql = 'SELECT COUNT(setting_id) FROM settings'
    result = query_db(sql)
    result = result[0]  # Finds the total number of settings
    settingcount = int(result[0])
    random_setting = random.randint(1, settingcount) # randomly chooses one setting_id
    sql = 'SELECT setting_name, setting_id FROM settings'
    result = query_db(sql)  # Gets a list of all settings with ids
    return render_template("setting_select.html", result=result, random_setting=random_setting) # Sends the list of settings and id for the random one

@app.route('/setting_list')
def setting_list():
    # Presents list of settings to choose from
    # Random option also available
    sql = 'SELECT COUNT(setting_id) FROM settings'
    result = query_db(sql)
    result = result[0]  # Finds the total number of settings
    settingcount = int(result[0])
    random_setting = random.randint(1, settingcount) # randomly chooses one setting_id
    sql = 'SELECT setting_name, setting_id FROM settings'
    result = query_db(sql)  # Gets a list of all settings with ids
    return render_template("iframe.html", result=result, random_setting=random_setting) # Sends the list of settings and id for the random one


@app.route('/setting/<int:id>')
def setting(id):
    # Reset answers and questions
    questions_list.clear()
    answers_list.clear()
    sql = f"""SELECT question_id
            FROM questions_bridge
            WHERE setting_id = {id};"""
    results = query_db(sql)
    for result in results:
        questions_list.append(int(result[0]))  # list of ints of question_ids
    # Gives information on the selected setting
    sql = """SELECT setting_name, setting_desc FROM settings
    WHERE setting_id = ?;"""
    result = query_db(sql, (id,), True)
    return render_template("setting_desc.html", result=result, id=id, first=0)

@app.route('/questions/<int:id>/<int:on_question>', methods=['GET', 'POST'])
def questions(id, on_question):  # id is the id of the setting. on_question is the location in the list of question ids of the current question id
    #  return f"on_question: {on_question}, questions_list: {questions_list}"
    if request.method == 'POST':
        prev_id = questions_list[on_question - 1]
        answer = request.form.get('choose_ans')
        sql = f"""SELECT game_logic.ans_explain, game_logic.ans_points 
                FROM game_logic
                JOIN answer_options ON game_logic.option_id=answer_options.option_id
                WHERE game_logic.setting_id = {id}
                AND game_logic.question_id = {prev_id}
                AND answer_options.answer_text = "{answer}";"""
        result = query_db(sql)
        result = result[0]
        answers_list.append(result[0])
        answers_list.append(result[1])
    # return f"on_question: {on_question}, questions_list: {questions_list}"
    question_count = count_questions(id) # returns int
    if int(on_question) < question_count:  # Continue if the questionid is valid
        current_id = questions_list[on_question]
        sql = f"""SELECT settings.setting_name, questions.question_text, answer_options.answer_text
        FROM questions_bridge
        JOIN settings ON questions_bridge.setting_id=settings.setting_id
        JOIN questions ON questions_bridge.question_id=questions.question_id
        JOIN answer_options ON questions_bridge.question_id=answer_options.question_id
        WHERE questions_bridge.setting_id={id}
        AND questions_bridge.question_id={current_id};"""  # Get the setting name, question text, and answer options
        result = query_db(sql)
        first = result[0] 
        return render_template("questions.html", result=result, question=first[1], id=id, nextid=on_question+1, answers_list=answers_list)
    else:  # If the questionid is not valid, aka all questions have been asked
        return render_template("scoring.html", answers_list=answers_list)
    
@app.route('/new_user', methods=['GET', 'POST'])
def new_user():
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username']
        hashed_pw = generate_password_hash(password)
        with sqlite3.connect(DATABASE) as db:
            cursor = db.cursor()
            sql = """INSERT INTO admin_login (username, encrypted_pw, authority_lvl)
            VALUES ('""" + username + "', '" + hashed_pw + "', 1);"
            cursor.execute(sql)
    return render_template("admin.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username']
        sql = """SELECT admin_login.username, admin_login.encrypted_pw
                FROM admin_login
                WHERE username = '""" + username + "';"
        results = query_db(sql)
        if results:
            result = results[0]
            if check_password_hash(result[1], password):
                return render_template("admin.html")
            else:
                return render_template("login.html", message='Incorrect Password')
        else:
            return render_template("login.html", message='Username not found')
    else:
        return render_template("login.html")
    

if __name__ == "__main__":
    app.run(debug=True)