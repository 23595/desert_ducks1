from flask import Flask, g, render_template
import sqlite3

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
    #Home page
    sql = 'SELECT setting_name, setting_id FROM settings'
    result = query_db(sql)
    return render_template("setting_select.html",result=result)

@app.route('/setting/<int:id>')
def setting(id):
    #Home page
    sql = """SELECT setting_name, setting_desc FROM settings
    WHERE setting_id = ?;"""
    result = query_db(sql, (id,), True)
    return str(result)

@app.route('/questions')
def questions():
    #Home page
    sql = """;"""
    result = query_db(sql)
    return str(result)



if __name__ == "__main__":
    app.run(debug=True)