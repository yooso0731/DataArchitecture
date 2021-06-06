from flask import Flask
from flask import request
import os
from src import mylogger, myconfig, mymodel
import pdb

app = Flask(__name__)

project_root_path = os.getenv("RECOMMEND_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
log_directory = cfg['logger'].get('log_directory')
loggers = dict()
loggers['recommend'] = mylogger.get_logger('recommend', log_directory)
loggers['tag'] = mylogger.get_logger('tag', log_directory)

@app.route('/recommend', methods=["POST"])
def recommend():
    name = request.json.get('book_name')
    author = request.json.get('author')
    logger.info('searching similar books with [ Book: {}, author: {} ]'.format(name, author))

    ret = {"result": None,
            "msg": ""}

    #isit = RecommendList 들어가서 name, author에 해당하는 document있는 지 확인, 출력하는 함수 생성 후 여기서 호출
    sim_result = mymodel.get_service1_result(name, author, loggers['recommend'])
    if not sim_result:
        ret["result"] = False
        ret["msg"] = "입력한 도서가 DB에 없습니다."
        loggers['recomend'].info(ret['msg'])
    else:
        ret["result"] = True
        ret["msg"] = sim_result.values()
        loggers['recommend'].info('[service1 result] Similar book list: {}'.format(ret['msg']))
    
    return ret



