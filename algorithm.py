"""
1. flask가 기본으로 실행되는 python 파일이 app.py인데, 이를 실행하고자하는 프로젝트 파이썬 파일(algorithm)로 변경
▶ set FLASK_APP=algorithm
2. 수정된 코드가 바로 반영되며 오류를 자세히 보여주는 디버그 모드 활성화
▶ set FLASK_DEBUG=1
3. flask 실행
▶ flask run
"""

# pip install cx_Oracle
# pip install Flask
# pip install pandas
# pip install scikit-learn
import cx_Oracle
from flask import Flask, request
from flask_cors import CORS
import json
from collections import Counter
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

"""
~~~ 데이터 전처리 ~~~
1. 로그인했을 때 store에 저장된 사용자 email을 react에서 flask로 전달
2. 로그인한 email에 해당되는 enter_list 추출
3. enter_list에서 가장 많은 tag 추출
4. 전체 문화예술 정보 info_list 저장
5. info_list와 enter_list를 left join해 사용자가 엔터리스트에 추가한 정보 제외


~~~ 콘텐츠 기반 필터링 추천 ~~~
1. TF-IDF(Term Frequency-Inverse Document Frequency) 벡터화
▶ TF-IDF : 단어의 빈도를 사용해 DTM(Document-Term Matrix : 문서 집합을 기반으로 각 문서에서 어떤 단어가 얼마나 나타나는지를 나타내는 행렬) 내의 각 단어들마다 중요한 정도를 가중치로 주는 방법
▶ 벡터화 : 행렬을 세로 벡터로 바꾸는 선형변환
2. cosine similarity
scikit-learn에서 지원하는 consine similarity 이용
"""

# Oralce DB 연결 설정
connection = cx_Oracle.connect('hr', 'a1234', 'localhost:1521/xe')

# Flask 어플리케이션 초기화
app = Flask(__name__)

# React에서(다른 도메인에서) Flask 리소스를 요청하고 공유할 수 있게 설정
CORS(app)

# React에서 로그인 버튼을 클릭하면 store에 저장되는 email을 'http://127.0.0.1/flask_login'로 보냄
@app.route('/flask_login', methods=['POST'])
def flask_login():
    # React에서 보낸 POST 요청의 JSON형식의 데이터를 'email'이라는 변수로 받음
    email = request.get_json()
    # print("React에서 로그인한 이메일 :", email)
    result_email = get_enter(email)
    return json.dumps(result_email)

def get_enter(email):
    # print('argument가 정상적으로 전달되었는지 확인 : ', email)
    cur = connection.cursor()
    enter_sql = "SELECT e.enter_seq, e.email, e.info_seq, i.title, i.tag FROM enterlist e, information i WHERE i.info_seq=e.info_seq and email = :email"   
    cur.execute(enter_sql, email)
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
        
    # enter_list에서 "tag" 값을 추출하여 카운트
    tag_counts = Counter([row['tag'] for row in enter_list])

    # "tag" 카운트를 기반으로 가장 많이 나타나는 태그를 찾음
    most_common_tag = max(tag_counts, key=tag_counts.get)

    print(f"가장 많이 등장하는 태그: {most_common_tag}")

    # 커서 다시 열기
    cur = connection.cursor()
    info_sql = "SELECT info_seq, title, tag, thumbnail, start_date, end_date FROM information" 
    cur.execute(info_sql)
    rows = cur.fetchall()
    cur.close()

    info_list = []
    for row in rows:
        info_dict = {
            'info_seq': row[0],
            'title': row[1], 
            'tag': row[2],
            'thumbnail' : row[3],
            'start_date' : row[4],
            'end_date' : row[5]
        }
        info_list.append(info_dict)


    # 리스트를 보기 좋게 표 형식의 데이터 프레임으로 변환
    enter_df = pd.DataFrame(enter_list)
    info_df = pd.DataFrame(info_list)

    # 공통 열을 기준으로 일치하지 않는 데이터 추출
    result_df = pd.merge(info_df, enter_df, how="left", indicator=True)
    result_df=result_df.query("_merge=='left_only'").drop(columns=["_merge"]).drop(columns=["enter_seq"]).drop(columns=["email"])
    #print("제외한 개수 : ",result_df.count())
    #print("엔터리스트 제외 information=====\n",result_df)

    # TF-IDF 벡터화
    tfidf_vectorizer = TfidfVectorizer()
    tag_tfidf_matrix = tfidf_vectorizer.fit_transform(result_df['tag'])

    # most_common_tag과 tag 간의 코사인 유사도 계산
    cosine_sim = cosine_similarity(tag_tfidf_matrix, tfidf_vectorizer.transform([most_common_tag]))

    # 계산한 코사인 유사도를 result_df의 컬럼으로 추가
    result_df['cosine_sim']=cosine_sim

    # 코사인 유사도가 가장 높은 4개의 데이터를 top_4라는 데이터 프레임으로 저장
    top_4 = result_df.sort_values(by='cosine_sim', ascending=False).head(4)

    #print(top_4)

    # top_4 데이터 프레임을 list로 변환
    algorithm_list = top_4.values.tolist()

    # print(algorithm_list)

    res_list = []
    for row in algorithm_list:
        algo_dict = {
            'info_seq': row[0],
            'title': row[1], 
            'tag': row[2],
            'thumbnail':row[3],
            'start_date' : str((row[4]).strftime("%Y-%m-%d")),
            'end_date' : str((row[5]).strftime("%Y-%m-%d")),
            'cosine_sim' : row[6],
        }
        res_list.append(algo_dict)

    print(res_list)
    return res_list

# 서버 실행
if __name__ == '__main__':
    app.run(host='127.0.0.1')
