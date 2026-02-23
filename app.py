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
    #Home page
    sql = """SELECT setting_name, setting_desc FROM settings
    WHERE setting_id = ?;"""
    result = query_db(sql, (id,), True)
    return render_template("setting_desc.html",result=result)

@app.route('/questions')
def questions():
    #Home page
    #sql = """;"""
    #result = query_db(sql)
    return render_template("layout.html")



if __name__ == "__main__":
    app.run(debug=True)