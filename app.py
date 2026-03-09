from flask import Flask, g, render_template
from flask import jsonify
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
    #Presents list of settings to choose from
    #Random option also available
    sql = 'SELECT COUNT(setting_id) FROM settings'
    result = query_db(sql)
    result = result[0] #Finds the total number of settings
    settingcount = int(result[0])
    random_setting = random.randint(1, settingcount) #randomly chooses one setting_id
    sql = 'SELECT setting_name, setting_id FROM settings'
    result = query_db(sql) #Gets a list of all settings with ids
    return render_template("setting_select.html",result=result,random_setting=random_setting) #Sends the list of settings and id for the random one

@app.route('/setting/<int:id>')
def setting(id):
    #Gives information on the selected setting
    sql = """SELECT setting_name, setting_desc FROM settings
    WHERE setting_id = ?;"""
    result = query_db(sql, (id,), True)
    return render_template("setting_desc.html",result=result,id=id,first=1)
    


@app.route('/questions/<int:id>/<int:questionid>')
def questions(id,questionid):
    sql = """SELECT COUNT(question_id) 
FROM questions_bridge
WHERE setting_id = 1;""" #Count the number of questions for the selected setting
    question_count = query_db(sql)
    question_count = question_count[0]
    question_count = int(question_count[0]) #Convert to int
    if questionid <= question_count: #Continue if the questionid is valid
        sql = """SELECT settings.setting_name, questions.question_text, answer_options.answer_text
        FROM questions_bridge
        JOIN settings ON questions_bridge.setting_id=settings.setting_id
        JOIN questions ON questions_bridge.question_id=questions.question_id
        JOIN answer_options ON questions_bridge.question_id=answer_options.question_id
        WHERE questions_bridge.setting_id=?
        AND questions_bridge.question_id=?;""" #Get the setting name, question text, and answer options
        result = query_db(sql, (id,questionid))
        first = result[0] 
        return render_template("questions.html", result=result, question=first[1], id=id, nextid=questionid+1)
    else: #If the questionid is not valid, aka all questions have been asked
        return render_template("scoring.html")
    
@app.route('/submit')
def submit():
    answer_text = request.args.get('chosenOption')
    return jsonify({answer_text})
    
if __name__ == "__main__":
    app.run(debug=True)