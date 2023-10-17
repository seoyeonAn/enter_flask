import cx_Oracle
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

import pandas as pd
import numpy as np

# Oralce DB 연결 설정
connection = cx_Oracle.connect('hr', 'a1234', 'localhost:1521/xe')

# Flask 어플리케이션 초기화
app = Flask(__name__)
CORS(app)
 
@app.route('/flask_login', methods=['POST'])
def flask_login():
    print('flask_login')
    email = request.get_json()
    # email = localstorage에 있는 email
    print("email from React :", email)
    result_email = get_enter(email)
    return json.dumps(result_email)
    #return jsonify(email)

#@app.route('/', methods=['GET'])
def get_enter(email):
    print('argument: ', email)
    cur = connection.cursor()
    
    # if email :
    #    sql = "SELECT * FROM enterlist WHERE email = :email"   
    #    cur.execute(sql, email)
    # else:
    #    sql = "SELECT * FROM enterlist"
    #    cur.execute(sql)

    # sql = """
    #     select e.enter_seq, e.email, i.info_seq, i.title, i.tag
    #     from enterlist e
    #     join information i on i.info_seq = e.info_seq
    #     WHERE email = :email
    # """

    if email :
        sql = """select e.enter_seq, e.email, i.info_seq, i.title, i.tag
         from enterlist e
         join information i on i.info_seq = e.info_seq
         WHERE email = :email"""   
        cur.execute(sql, email)
    else:
        sql = "SELECT * FROM enterlist"
        cur.execute(sql)

    # sql ="""
    # SELECT * FROM enterlist WHERE email = :email
    # """
    # cur.execute(sql, email)
    
    rows = cur.fetchall()
    cur.close()

    enter_info_list = []
    for row in rows:
        enter_info_dict = {
            'enter_seq': row[0],
            'email': row[1],
            'info_seq': row[2],
            'title': row[3],
            'tag': row[4]
        }
        enter_info_list.append(enter_info_dict)

    print(enter_info_list)
    print(type(json.dumps(enter_info_list)))    
    #return json.dumps(enter_list)
    return enter_info_list

# 서버 실행
# debug=True가 잘 안먹히므로 set FLASK_DEBUG=1 설정 후 flask run
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)