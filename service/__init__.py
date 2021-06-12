# -- coding: utf-8 --

from flask import Flask, render_template
from flask import request
from bson import json_util
import json
import os
from src import mylogger, myconfig, myapi
import pdb

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

project_root_path = os.getenv("RECOMMEND_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
log_directory = cfg['logger'].get('log_directory')
loggers = dict()
loggers['recommend'] = mylogger.get_logger('recommend', log_directory)
loggers['tag'] = mylogger.get_logger('tag', log_directory)
loggers['check'] = mylogger.get_logger('check', log_directory)

@app.route("/recommend", methods=["POST"])
def recommend():
    """recommend book API function

    Specification can be found in `wiki` tab

    :return: JSON serialized string contatiningthe result with recommend book
    :rtype: str
    """
    
    book_name = request.json.get('book_name')
    author = request.json.get('author')
   # loggers['recommend'].info('searching similar books with [ Book: {}, author: {} ]'.format(name, author))

    ret = {"result": None,
            "msg": ""}

    #isit = RecommendList 들어가서 name, author에 해당하는 document있는 지 확인, 출력하는 함수 생성 후 여기서 호출
    sim_result = myapi.get_recommend(book_name, author, loggers['recommend'])
    if not sim_result:
        ret["result"] = False
        ret["msg"] = "입력한 도서가 DB에 없습니다."
        loggers['recommend'].info(ret['msg'])
    else:
        ret["result"] = True
        ret["msg"] = sim_result
       # loggers['recommend'].info('[service1 result] Similar book list: {}'.format(ret['msg']))
       
    return ret

@app.route('/tag', methods=["POST"])
def tag():
    """ tag API function.

    Specification can be found in `wiki` tab

    :return: JSON serialized string containing rags of a book
    :rtype: str
    """
    book_name = request.json.get('book_name')
    author = request.json.get('author')
    #loggers['tag'].info('{} - {} Searching similar books'.format(book_name, author))

    ret = {"result": None }

    get_tag = myapi.get_tags(book_name, author, loggers['tag'])
    if not get_tag:
        ret["result"] = False
        ret["msg"] = "입력한 도서가 DB에 없습니다."
        loggers['tag'].info(ret['msg'])
    else:
        ret["result"] = True
        ret["get_tag"] = get_tag    

    return ret

@app.route('/in_db', methods=['POST'])
def in_db():
    """ Checking book in DB API function.

    Specification can be found in `wiki` tab

    :return: JSON serialized string containing rags of a book
    :rtype: str
    """
    book_name = request.json.get('book_name')
    author = request.json.get('author')
    
    ret = {"result": None}
    
    check = myapi.book_in_DB(book_name, author, loggers['check'])
    if not check:
        ret["result"] = False
        ret["msg"] = "입력한 도서는 DB에 없습니다."
        loggers['check'].info(ret['msg'])
    else:
        ret["result"] = True
        ret["msg"] = "DB에 존재합니다. -- Book ID: {}".format(check)
        loggers['check'].info(ret['msg'])
     
    return ret


@app.route('/')
def main():
    return render_template("index.html")


@app.route("/search-book", methods=["POST"])
def search_book():
    '''
    name = request.values.get("book_name")
    author = request.values.get("author")
    #console.log(name)
    return render_template("search_failed.html")
    '''
    """recommend book API function
    Specification can be found in 'wiki' tab
    """

    
    book_name = request.values.get("book_name")
    author = request.values.get("author")

    ret = {"result": None, "msg": ""}
   # return ret

    sim_result = myapi.get_recommend(book_name, author, loggers['recommend'])
    if not sim_result:
        ret["result"] = False
        ret["msg"] = "입력한 도서가 DB에 없습니다."
        #loggers['recommend'].info(ret['msg'])
        
    else:
        ret["result"] = True
        ret["msg"] = sim_result
        
    loggers["recommend"].info(len(sim_result))
    ## value 만들어서 넘기기
    '''
    fin_result = {}
    for i in range(len(sim_result)):
        fin_result[i] = {"name": sim_result[i]['name'],
                    "author": sim_result[i]['author'],
                    "score": sim_result[i]['score'],
                    "tags": sim_result[i]['tags']}
    '''
    #loggers["recommend"].info(ret["msg"])
    #return render_template("search_failed.html")

    if not ret["result"]:
        return render_template("search_failed.html")
    
    ret_json = json.dumps(ret, ensure_ascii=False)
    
    return render_template("result.html", sim_info=ret_json)
