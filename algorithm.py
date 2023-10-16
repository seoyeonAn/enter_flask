import cx_Oracle
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from collections import Counter

import pandas as pd

#pip install scikit-learn
# 코사인 유사도
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# AST모듈의 literal_eval을 사용하여 str타입을 list타입으로 변경
# tag가 여러 개인 것을 list로 변경
from ast import literal_eval

# Oralce DB 연결 설정
connection = cx_Oracle.connect('hr', 'a1234', 'localhost:1521/xe')

# Flask 어플리케이션 초기화
app = Flask(__name__)
CORS(app)

@app.route('/flask_login', methods=['POST'])
def flask_login():
    email = request.get_json()
    #print("React에서 로그인한 이메일 :", email)
    result_email = get_enter(email)
    return json.dumps(result_email)

def get_enter(email):
    # argument가 정상적으로 전달되었는지 확인
    #print('argument 확인 : ', email)
    cur = connection.cursor()
    sql = "SELECT e.enter_seq, e.email, e.info_seq, i.title, i.tag FROM enterlist e, information i WHERE i.info_seq=e.info_seq and email = :email"   
    cur.execute(sql, email)
    rows = cur.fetchall()
    cur.close()

    enter_list = []
    for row in rows:
        enter_dict = {
            'enter_seq': row[0],
            'email': row[1],
            'info_seq': row[2],
            'title': row[3],
            'tag': row[4],
        }
        enter_list.append(enter_dict)
    # 리스트를 데이터 프레임으로 변환
    enter_df = pd.DataFrame(enter_list)

    # 결과에서 "tag" 값을 추출하여 카운트
    tag_counts = Counter([row['tag'] for row in enter_list])

    # "tag" 카운트를 기반으로 가장 많이 나타나는 태그를 찾음
    most_common_tag = max(tag_counts, key=tag_counts.get)

    # 결과 출력
    print(f"가장 많이 등장하는 태그: {most_common_tag}")

    # 커서 다시 열기
    cur = connection.cursor()
    #sql2 = "SELECT info_seq, title, tag, start_date, end_date, thumbnail FROM information"
    sql2 = "SELECT info_seq, title, tag FROM information" 
    cur.execute(sql2)
    rows = cur.fetchall()
    cur.close()

    info_list = []
    for row in rows:
        info_dict = {
            'info_seq': row[0],
            'title': row[1], 
            'tag': row[2],
            # 'start_date' : row[3],
            # 'end_date' : row[4],
            # 'thumbnail' : row[3]
        }
        info_list.append(info_dict)

    info_df = pd.DataFrame(info_list)

    # 전체 information DF에서 로그인한 사용자의 엔터리스트 DF 빼기
    # 사용자가 이미 엔터리스트에 추가했던 정보는 추천하지 않기 위한 작업

    # 공통 열을 기준으로 일치하지 않는 데이터 추출
    result_df = pd.merge(info_df, enter_df, how="left", indicator=True)
    result_df=result_df.query("_merge=='left_only'").drop(columns=["_merge"]).drop(columns=["enter_seq"]).drop(columns=["email"])
    #print("제외한 개수 : ",result_df.count())
    #print("엔터리스트 제외 information=====\n",result_df)

    # 공백을 기준으로 구분되는 문자열로 변환
    #result_df['tag'] = result_df['tag'].apply(lambda x : (' ').join(x))

    #result_df['tag'] = result_df['tag'].apply(literal_eval)
    result_df['tag']


    # 가장 많이 언급된 most_common_tag을 추가해 TF-IDF 백터화
    result_df['tag'] = ''+result_df['tag']+''.join(most_common_tag)
    
    # TF-IDF 벡터화
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(result_df['tag'])

    # 코사인 유사도 계산
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    print(cosine_sim)
    # 코사인 유사도 행렬에서 가장 유사도가 높은 4개 추천
    indices = cosine_sim[0].argsort()[-5:-1][::-1]  # 제일 높은 유사도 순으로 정렬하고 상위 4개 추출

    recommended_data = result_df.iloc[indices]
    print(recommended_data)

    return enter_list

# 서버 실행
# debug=True가 잘 안먹히므로 set FLASK_DEBUG=1 설정 후 flask run
if __name__ == '__main__':
    app.run(host='127.0.0.1')


