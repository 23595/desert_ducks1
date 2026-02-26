from flask import Flask, g, render_template
import sqlite3
import random

DATABASE = 'ducks.db'

#initialise app
app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

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
    #Home page
    return render_template("homepage.html")

@app.route('/setting_select')
def setting_select():
    sql = 'SELECT COUNT(setting_id) FROM settings'
    result = query_db(sql)
    result = result[0]
    settingcount = int(result[0])
    random_setting = random.randint(1, settingcount)
    sql = 'SELECT setting_name, setting_id FROM settings'
    result = query_db(sql)
    return render_template("setting_select.html",result=result,random_setting=random_setting)

@app.route('/setting/<int:id>')
def setting(id):
    sql = """SELECT setting_name, setting_desc FROM settings
    WHERE setting_id = ?;"""
    result = query_db(sql, (id,), True)
    #Get the first question ready
    sql = """SELECT questions.question_id FROM questions
JOIN questions_bridge ON questions.question_id=questions_bridge.question_id
WHERE questions_bridge.setting_id = ?;"""
    questions = query_db(sql, (id,))
    question_list = []
    for i in questions:
        question_list.append(i[0])
    return render_template("setting_desc.html",result=result,question_list=question_list,id=id,first=question_list[0])
    


@app.route('/questions/<int:id>/<int:questionid>')
def questions(id,questionid):
    sql = """SELECT settings.setting_name, questions.question_text, answer_options.answer_text
FROM questions_bridge
JOIN settings ON questions_bridge.setting_id=settings.setting_id
JOIN questions ON questions_bridge.question_id=questions.question_id
JOIN answer_options ON questions_bridge.question_id=answer_options.question_id
WHERE questions_bridge.setting_id=?
AND questions_bridge.question_id=?;"""
    result = query_db(sql, (id,questionid))
    first = result[0]
    sql = """SELECT questions.question_id 
    FROM questions
    JOIN questions_bridge 
    ON questions.question_id=questions_bridge.question_id
    WHERE questions_bridge.setting_id = """ + str(id) + ';'
    question_ids = query_db(sql)
    question_id_list = []
    for x in question_ids:
        question_id_list.append(x[0])
    return render_template("index.html", result=result, question=first[1], id=id, question_id_list=question_id_list)



if __name__ == "__main__":
    app.run(debug=True)