import pymongo
from pymongo import MongoClient
from src import mylogger, myconfig
import numpy as np
import pdb
import os

project_root_path = os.getenv("RECOMMEND_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))
db_ip = cfg['db']['ip']
db_port = int(cfg['db']['port'])
db_name = cfg['db']['name']


def get_recommend(book_name, author, logger):
    """Get recommend book list 

    :param book_name: book name for search similar book
    :type book_name: str
    :param author: book author for search similar book
    :type author: str
    :param logger: logger instance
    :type logger: logging.Logger
    :return: [{sim_book_id: _, score: _, tags: []}]
    :rtype: list
    """
    db_client = MongoClient(db_ip, db_port)
    db = db_client[db_name]
    
    col_book = db[cfg['db']['col_book']]
    col_recommend = db[cfg['db']['col_recommend']]
    
    result = {}
    doc_book = col_book.find_one({"name": book_name, "author": author})

    if not doc_book:
        db_client.close()
        logger.info('[Book: {}, Author: {}] 해당 도서가 DB에 없습니다.'.format(book_name, author))
        return result

    doc_recommend = col_recommend.find_one({"Book": doc_book['_id']})
    
    if not doc_recommend:
        db_client.close()
        logger.info('[Book: {}, Author: {}] 해당 도서와 유사한 추천 도서가 없습니다.'.format(book_name, author))
        return result

    recommend_list = doc_recommend['similar_list']
    result = recommend_list
    db_client.close()
    
    return result


def get_tags(book_name, author, logger):
    """Get tags of the input book (searching)
    
    :param book_name: book name for search similar book
    :type book_name: str
    :param author: book author for search similar book
    :type author: str
    :param logger: logger instance
    :type logger: logging.Logger
    :return: tags of the search book [('tag', score), ...]
    :rtype: list
    """
    db_client = MongoClient(db_ip, db_port)
    db = db_client[db_name]

    col_book = db[cfg['db']['col_book']]
    col_tag = db[cfg['db']['col_tag']]

    doc_book = col_book.find_one({"name": book_name, "author": author})
    doc_tag = col_tag.find_one({"Book": doc_book['_id']})

    if not doc_tag:
        db_client.close()
        result = None
        return result
    else:
        result = doc_tag['tags']
        db_client.close()
        return result


def book_in_DB(book_name, author, logger):
    """Return information about if input book is in DB  

    :param book_name: book name for search similar book
    :type book_name: str
    :param author: book author for search similar book
    :type author: str
    :param logger: logger instance
    :type logger: logging.Logger
    :return: if book in DB: book id. else: None
    :rtype: str
    """
    db_client = MongoClient(db_ip, db_port)
    db = db_client[db_name]
    
    col_book = db[cfg['db']['col_book']]

    doc_book = col_book.find_one({"name": book_name, "author": author})

    if not doc_book:
        result = None
    else:
        result = doc_book['_id']
        
    db_client.close()
    return result
