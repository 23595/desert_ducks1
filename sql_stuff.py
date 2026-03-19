import sqlite3

DATABASE = 'ducks.db'

def query_db(sql):
    with sqlite3.connect(DATABASE) as db:
        cursor = db.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        return results

#For every setting, go through each question and each answer and add ans_points of ten and ans_explain of the setting, question, answer to the game_logic table

if __name__ == "__main__":
    sql = 'SELECT settings.setting_id, settings.setting_name FROM settings'
    settingid_list = query_db(sql)
    for settingid in settingid_list:  #For each setting pair
        settingname = settingid[1]
        settingid = settingid[0]
        sql = """SELECT questions_bridge.question_id, questions.question_text 
                FROM questions_bridge
                JOIN questions ON questions_bridge.question_id = questions.question_id 
                WHERE questions_bridge.setting_id = """ + str(settingid) + ";"
        questionid_list = query_db(sql)
        for questionid in questionid_list: #For each question
            questiontext = questionid[1]
            questionid = questionid[0]
            sql = "SELECT option_id, answer_text FROM answer_options WHERE question_id = " + str(questionid) + ";"
            optionid_list = query_db(sql)
            for optionid in optionid_list: #For each possible answer
                optiontext = optionid[1]
                optionid = optionid[0]
                #sql = """INSERT INTO game_logic (setting_id, question_id, option_id, ans_points, ans_explain)
                #        VALUES (""" + str(settingid) + ", " + str(questionid) + ", " + str(optionid) + ", 10, '"
                #sql = sql + f"{settingname[:5]} {questiontext[:5]} {optiontext[:5]}';"
                sql = f"""INSERT INTO game_logic (setting_id, question_id, option_id, ans_points, ans_explain)
                        VALUES ({settingid}, {questionid}, {optionid}, 10, '{settingname[:5]} {questiontext[:5]} {optiontext[:5]}');"""
                with sqlite3.connect(DATABASE) as db:
                    cursor = db.cursor()
                    cursor.execute(sql)