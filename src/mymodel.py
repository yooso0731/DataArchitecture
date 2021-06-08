import pymongo
from pymongo import MongoClient
from src import mylogger, myconfig
import numpy as np
import pdb
import os

class model1:
    """Model for service1
    """
    def compute_similarity(self, data, logger, N):
        """Compute similarities between books, and return topN books

        :param data: dictionary of book tags {book id: [(tag, score), ...], ...}
        :type data: dict
        :param logger: logger instance
        :type logger: logging.Logger
        :param N: # of saving similar book
        :type N: int
        :return: dictionary of book tags TopN {book_id: [(similar book_id, score, [same tag list]), ...]}
        :rtype: dict
        """
        total_sim = {}
        book_ids = list(data.keys())
        book_tags = list(data.values())
        
        for i in range(0, len(book_ids)):
            sim_score = []
            for ii in range(0, len(book_ids)): 
                if i == ii: continue 
                # compute similarities    
                total_score = 0
                sum_score = 0
                compare_tags = [tag for (tag, score) in book_tags[ii]]
                intersection = []
                
                for (tag, score) in book_tags[i]:
                    intersection.append(tag)
                    total_score += score
                    if tag in compare_tags:
                        sum_score += score
                        
                sim = float(sum_score / total_score)
                sim_score.append((book_ids[ii], sim, intersection))
                
            sim_score.sort(key = lambda x: -x[1])
            total_sim[book_ids[i]] = sim_score[0:N]
            logger.info('Finish computing similarities of Book ID: {}'.format(book_ids[i]))
            
        return total_sim


def run_model1(logger, N=5):
    """Run model1 
        
    :param logger: logger instance
    :type logger: logging.Logger
    :param N: # of saving similar book (default 5)
    :type N: int
    """
    project_root_path = os.getenv("RECOMMEND_SERVER")
    cfg = myconfig.get_config("{}/share/project.config".format(project_root_path))
    db_ip = cfg['db']['ip']
    db_port = int(cfg['db']['port'])
    db_name = cfg['db']['name']
    
    db_client = MongoClient(db_ip, db_port)
    db = db_client[db_name]
    
    col_tag = db[cfg['db']['col_tag']]
    col_book = db[cfg['db']['col_book']]
    col_recommend = db[cfg['db']['col_recommend']]
    
    #prepare data
    doc_tags = col_tag.find()
    input_data = {}
    for doc_tag in doc_tags:
        input_data[doc_tag['Book']] = doc_tag['tags']
    
    # run model1
    m1 = model1()
    data = m1.compute_similarity(input_data, logger, N)
    
    for book_id, value in data.items():
        doc_recommend = col_recommend.find_one({"Book": book_id})
        
        if not doc_recommend:
            col_recommend.insert_one(
            {"Book": book_id, "similar_list": []})
            logger.info('Book Id: {} -- Start adding similar book'.format(book_id))
            for sim_book_id, score, tags in value:
                doc_book = col_book.find_one({"_id": sim_book_id}) # name, author
                col_recommend.update_one({"Book": book_id},
                        {"$push": {"similar_list": {
                            "name": doc_book["name"],
                            "author": doc_book["author"],
                            "score": score, 
                            "tags": tags}}})
                logger.info('new similar book {}, score: {}'.format(sim_book_id, score))
        
        else:
            logger.info('Book Id: {} -- Start changing similar book'.format(book_id))
            sim_list = []
            for sim_book_id, score, tags in value:
                doc_book = col_book.find_one({"_id": sim_book_id})
                temp = {"name": doc_book["name"], 
                        "author": doc_book["author"],
                        "score": score,
                        "tags": tags}
                sim_list.append(temp)
                
            col_recommend.update_one(
             {"Book": book_id},
             {"$set": {"similar_list": sim_list} })
            #logger.info('{} -- update similar book {}, score: {}'.format(book_id, sim_book_id, score))

        
    db_client.close()

project_root_path = os.getenv("RECOMMEND_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
db_ip = cfg['db']['ip']
db_port = int(cfg['db']['port'])
db_name = cfg['db']['name']

def get_service1_result(book_name, author, logger):
    """Get stuff for service 1

    :param book_name: book name for search similar book
    :type book_name: str
    :param author: book author for search similar book
    :type author: str
    :param logger: logger instance
    :type logger: logging.Logger
    :return: {book_id: [{sim_book_id: _, score: _, tags: []}]}
    :rtype: dict
    """
    db_client = MongoClient(db_ip, db_port)
    db = db_client[db_name]
    
    col_book = db[cfg['db']['col_book']]
    col_recommend = db[cfg['db']['col_recommend']]
    
    result = {}
    doc_book = col_book.find_one({"name": book_name, "author": author})

    if not doc_book:
        db_client.close()
        logger.info('[Book: {}, Author: {}] -- DB에 없습니다.'.format(book_name, author))
        return result

    doc_recommend = col_recommend.find_one({"Book": doc_book['_id']})
    
    if not doc_recommend:
        db_client.close()
        logger.info('[Book: {}, Author: {}] -- 추천도서가 없습니다.'.format(book_name, author))
        return result

    recommend_list = doc_recommend['similar_list']
    #result[book_id] = recommend_list
    result = recommend_list

    return result
    '''
    if len(recommend_list) >= 2:
        #
    else: 
        result[book_id] = recommend_list
    '''

def get_service2_result(book_name, author, logger):
    """Get stuff for service2

    """
    db_client = MongoClient(db_ip, db_port)
    db = db_client[db_name]

    col_book = db[cfg['db']['col_book']]
    col_tag = db[cfg['db']['col_tag']]

    doc_book = col_book.find_one({"name": book_name, "author": author})
    doc_tag = col_tag.find_one({"Book": doc_book['_id']})

    result = {}
    if not doc_tag:
        db_client.close()
        logger.info('[Book: {}, Author: {}] -- DB에 없음'.format(book_name, author))
        return result
    else:
        result = doc_tag['tags']
        return result

