# -- coding: utf-8 --

from flask import Flask
from flask import request
import os
from src import mylogger, myconfig, mymodel
import pdb

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

project_root_path = os.getenv("RECOMMEND_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
log_directory = cfg['logger'].get('log_directory')
loggers = dict()
loggers['recommend'] = mylogger.get_logger('recommend', log_directory)
loggers['tag'] = mylogger.get_logger('tag', log_directory)

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
    sim_result = mymodel.get_service1_result(book_name, author, loggers['recommend'])
    if not sim_result:
        ret["result"] = False
        ret["msg"] = "입력한 도서가 DB에 없습니다."
        loggers['recommend'].info(ret['msg'])
    else:
        ret["result"] = True
        ret["msg"] = sim_result
       # loggers['recommend'].info('[service1 result] Similar book list: {}'.format(ret['msg']))
       
    return ret

'''
    ret["result"] = True
    msg = ""
    if len(sim_result) >= 2:
        for i in range(len(sim_result)):
            mag += sim_result
    return ret
    '''

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

    ret = {"result": None,
            }

    get_tag = mymodel.get_service2_result(book_name, author, loggers['tag'])
    if not get_tag:
        ret["result"] = False
        ret["msg"] = "입력한 도서가 DB에 없습니다."
        loggers['tag'].info(ret['msg'])
    else:
        ret["result"] = True
        ret["get_tag"] = get_tag    

    return ret
