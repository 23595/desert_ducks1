from flask import Flask, g, render_template, request
import json
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
        if len(answers_list) > 2 * (on_question):
            del answers_list[-1]
            del answers_list[-1]
        return render_template("questions.html", result=result, question=first[1], id=id, nextid=on_question+1, answers_list=answers_list)
    else:  # If the questionid is not valid, aka all questions have been asked
        if len(answers_list) > 2 * (on_question):
            del answers_list[-1]
            del answers_list[-1]
        total = 0
        for i in range(len(answers_list)):
            if i % 2 == 0:
                pass
            else:
                total += int(answers_list[i])
        return render_template("scoring.html", answers_list=answers_list, total=total)
    
@app.route('/new_user', methods=['GET', 'POST'])
def new_user():
    error_message = ''
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username']
        check_password = request.form['password_confirm']
        # Find existing usernames to prevent overlap
        sql = "SELECT username FROM admin_login WHERE username = '" + username + "';"
        overlap = query_db(sql)
        if overlap:
            error_message = 'Username already exists.'
            return render_template("admin.html", error_message=error_message) # Returns an error message if the username already exists
        elif len(username) < 4:
            error_message = 'Username must be at least 4 characters'
            return render_template("admin.html", error_message=error_message) # Returns an error message if the username is too short
        elif len(password) < 4:
            error_message = 'Password must be at least 4 characters'
            return render_template("admin.html", error_message=error_message) # Returns an error message if the password is too short
        elif check_password != password:
            error_message = 'Passwords did not match. Ensure that Password and Confirm Password are the same.'
            return render_template("admin.html", error_message=error_message) # Returns an error message if the passwords do not match
        else:
            hashed_pw = generate_password_hash(password)
            with sqlite3.connect(DATABASE) as db:
                cursor = db.cursor()
                sql = """INSERT INTO admin_login (username, encrypted_pw, authority_lvl)
                VALUES ('""" + username + "', '" + hashed_pw + "', 1);"
                cursor.execute(sql)
    return render_template("admin.html", error_message=error_message)
    
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
                sql = """SELECT settings.setting_name, questions.question_text
FROM questions_bridge
JOIN settings ON questions_bridge.setting_id=settings.setting_id
JOIN questions ON questions_bridge.question_id=questions.question_id;"""
                setting_question = query_db(sql)
                data_dict = {}
                for setting, question in setting_question:
                    if setting not in data_dict:
                        data_dict[setting] = []
                    data_dict[setting].append(question)
                sql = """SELECT settings.setting_name, questions.question_text, answer_options.answer_text, game_logic.ans_points, game_logic.ans_explain
                    FROM game_logic
                    JOIN settings ON game_logic.setting_id=settings.setting_id
                    JOIN answer_options ON game_logic.option_id=answer_options.option_id
                    JOIN questions ON game_logic.question_id=questions.question_id;"""
                results = query_db(sql)
                everything_dict = {}
                for set, ques, ans_txt, ans_pts, ans_ex in results:
                    if set not in everything_dict:
                        everything_dict[set] = {}
                    if ques not in everything_dict[set]:
                        everything_dict[set][ques] = {}
                    everything_dict[set][ques][ans_txt] = [ans_pts, ans_ex]
                return render_template("admin.html", setting_names=data_dict.keys(), setting_data=json.dumps(data_dict), everything=json.dumps(everything_dict), error_message='')  # go to admin page
            else:
                return render_template("login.html", message='Incorrect Password')  # Gives error message
        else:
            return render_template("login.html", message='Username not found')  # Gives error message
    else:
        return render_template("login.html")
    

if __name__ == "__main__":
    app.run(debug=True)