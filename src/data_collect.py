import os
import pdb
import re
from tqdm import tqdm

from bs4 import BeautifulSoup as bs
import collections
from konlpy.tag import Hannanum, Okt, Mecab
import numpy as np
from pymongo import MongoClient
import requests

from src.textrank import TextRank
from src import myconfig

# DB
project_root_path = os.getenv("RECOMMEND_SERVER")
cfg = myconfig.get_config('{}/share/project.config'.format(project_root_path))

db_ip = cfg['db']['ip']
db_port = int(cfg['db']['port'])
db_name = cfg['db']['name']

db_client = MongoClient(db_ip, db_port)
db = db_client[db_name]

col_book = db[cfg['db']['col_book']]
col_tag = db[cfg['db']['col_tag']]


def crawl_book(logger, startPage=1, endPage=5, s_type="best"):
    """Collect data from www.yes24.com
    
    :param logger: logger instance
    :type logger: logging.Logger
    :param startPage: start page of crawling (default 1, 1 page contains 40 book list)
    :type startPage: int
    :param endPage: last page of crawling (default 5)
    :type endPage: int
    :param s_type: sort type, "best" or "new" (default best)
    :type s_type: str
    :return: pairs of {book name_author: {book info...}}
    :rtype: dict
    """
    s_type = "04" if s_type == "new" else "05"
    country = 1 # book country code (1~10)
    c_category = ['한국', '영미', '일본', '중국', '프랑스', '독일', '러시아', '스페인, 중남미', '북유럽', 'etc']
    del_pattern = "\[.*\]|\(.*\)|\s-\s.*" # delete pattern in book name
    
    book_info = {}
    n_got = 0
    
    while country < 11:
        logger.info('Starting crawl {}소설 -- {}/10 '.format(c_category[country-1], country))

        for page_num in tqdm(range(startPage, endPage + 1)):
            root_url = ("http://www.yes24.com/24/Category/Display/0010010460%02d" % country) + \
            "?FetchSize=40&ParamSortTp={}&PageNumber={}".format(s_type, str(page_num))
    
            res = requests.get(root_url) 
            html = res.text
            soup = bs(html, 'html.parser')
            book_list = soup.select('div.goods_info > div.goods_name > a')
            
            if len(book_list) == 0:
                break
                
            for index in range(len(book_list)):
                if not book_list[index].text:  # if book name is empty
                    continue
                
                name = re.sub(del_pattern, '', book_list[index].text).strip()
                href = book_list[index]['href']
                info_url = "http://www.yes24.com/" + href
            
                res_info = requests.get(info_url)
                if res_info.status_code != 200:
                    continue

                html_ = res_info.text
                soup_ = bs(html_, 'html.parser')
        
                author = soup_.select('span.gd_pubArea > span.gd_auth > a')
                author_list = []
                if not author:
                    continue
                elif len(author) > 2:
                    for i in range(0, len(author)):
                        author_list.append(author[i].text)
                    author = ', '.join(author_list)
                else:
                    author = author[0].text
               
                p_date = soup_.select('span.gd_date')[0].text
                intro = soup_.select('div.infoWrap_txt')[0].text
                try:
                    p_review = soup_.select('#infoset_pubReivew > div.infoSetCont_wrap > div.infoWrap_txt')[0].text
                except: p_review = ' '

                book_info[name + '_' + author] = {"p_date": p_date, "intro": intro, "p_review": p_review}
                n_got += 1
            
        country += 1
    
    logger.info('Collect {} Book information in all country categories'.format(len(book_info.keys())))
    return book_info

def create_tag(book_info, logger, using='mecab', N=15):
    """Create tags using 'intro'+'p_review' of crawl_book() output 
    
    :param book_info: dictionary of {'book name_author': {"p_date": "...", "intro": "...", "p_review": "..."}, ...}
    :type book_info: dict
    :param logger: logger instance
    :type logger: logging.Logger
    :param using: use konlpy.tag name, choice=['mecab', 'hannanum', 'okt']
    :type using: str 
    :return: dictionary of {"book name_author": [("tag1", score), ...]}
    :rtype: dict
    """
    stopwords = ['소설', '소설가', '문학', '평론가']
    book_tag = {}

    if using == 'mecab': using = Mecab()
    elif using == 'hannanum': using = Hannanum()
    else: using = Okt()

    for k, v in book_info.items():
        info_sentence = []
        book_info = v['intro'] + v['p_review']

        # delete stopwords
        for word in stopwords:
            book_info = re.sub(word, '', book_info)
        
        # split sentences
        sentences = book_info.split('.')
        [info_sentence.append(s.strip()) for s in sentences if s]

        for i in range(len(info_sentence)):
            # cleansing
            clean = re.sub('[^가-힣 ]', ' ', str(info_sentence[i]))
            info_sentence[i] = ' '.join(using.nouns(clean))
        
        try:
            textrank = TextRank(info_sentence)
            tags = [(tag, round(score, 3)) for tag, score in textrank.keywords(N).items()]
        
            book_tag[k] = tags
            logger.info('Create tags of [Book id: {}]'.format(k))
        except:
            logger.info('Book id: {} -- No tags'.format(k))
        
    return book_tag


def save_to_Book(book_info, logger):
    """Save the given book info in Book Collection
    
    :param book_info: {book name_author: {book info}} pairs
    :type book_info: dict
    :param logger: logger instance
    :type logger: logging.Logger
    """
    for book in book_info.keys():
        # Insert the book information data if not exists.
        name, author = book.split('_')
        
        if not name or not author:
            continue

        doc_book = col_book.find_one({"name":name, "author":author})
        if not doc_book: 
            col_book.insert_one({
                "name": name, "author": author, 
                "p_date": book_info[book]["p_date"], "intro": book_info[book]["intro"]
                })
            logger.info('Insert new data in Book DB -- [Book: {}]'.format(name))
        else:
            logger.info('Update data in Book DB [Book: {}]'.format(name)) 
                
                
def save_to_Tag(tag_data, logger):
    """Save the given book tags in Tag Collection
    
    :param book_info: {book name_author: [(tag, score), ...]} pairs
    :type book_info: dict
    :param logger: logger instance
    :type logger: logging.Logger
    """
    
    for book, tags in tag_data.items():
        name, author = book.split('_')
        
        if not name or not author: return False
        
        doc_book = col_book.find_one({"name": name, "author": author})
        doc_tag = col_tag.find_one({"Book": doc_book['_id']})
        
        if not doc_tag:
            col_tag.insert_one({"Book": doc_book['_id'], "tags": tags})
            logger.info('Insert new data in Tag DB -- [Book: {}]'.format(name))
        else:
            col_tag.update_one({"Book": doc_book['_id']},
                    {"$set": {"tags": tags}
                    })
            logger.info('Update data in Tag DB [Book: {}]'.format(name))        
