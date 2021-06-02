import requests
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
import pdb
from tqdm import tqdm
from src import myconfig
import os
import re
from konlpy.tag import Hannanum, Okt, Mecab
import collections
import numpy as np

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
    """Collect data from www.yes24.com and store it to Book Collection
    
    :param logger: logger instance
    :type logger: logging.Logger
    :param startPage: start page of crawling (default 1)
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
    del_pattern = "\(.*\)|\s-\s.*" # delete pattern in book name(title)

    book_info = {}
    n_got = 0

    #while country < 2: #test ver
    while country < 11:
        logger.info('Starting crawl coutry category -- {}/10'.format(country))

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
                if not book_list[index].text:
                    continue

               # name = book_list[index].text
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

                #logger.info('{} -- Add book count'.format(n_got))
                book_info[name + '_' + author] = {"p_date": p_date, "intro": intro, "p_review": p_review}
                n_got += 1
            
        country += 1
    
    logger.info('{} items collected.'.format(n_got))
    logger.info('[crawling] save dict -- {}'.format(len(book_info.keys())))
    return book_info


def create_tag(book_info, logger, using='mecab'):
    """Create tags using frequency analysis
    
    :param book_intro: pairs of {'book name_author': {"intro": "...", "p_review": "..."}}
    :type s_type: dict
    :param logger: logger instance
    :type logger: logging.Logger
    :param using: use konlpy.tag  choice=['mecab', 'hannanum', 'okt']
    :type using: str 
    :return: pairs of {"book_name": tag list}
    :rtype: dict
    """  
    book_tag = {}

    if using == 'mecab':
        using = Mecab()
    elif using == 'hannanum':
        using = Hannanum()
    else:
        using = Okt()
    
    get_book = len(book_info.keys())
    logger.info('[create_tag] get book -- {}'.format(get_book))

    n_tag = 0
    for k, v in book_info.items():
        book_info = v['intro'] + v['p_review']
        
        # extract korean
        cleans = re.sub('[^가-힣 ]', ' ', str(book_info))
        # extract nouns
        data_nouns = using.nouns(cleans)  
        
        frequency = collections.Counter(data_nouns)
        '''
        # create threshold on frequency
        temp = set([int(v) for k, v in frequency.items()]) #) if v > 1])
        #threshold = np.median(list(temp))
        threshold = np.mean(list(temp))
        '''
        ## 시도2 top 10개 뽑기
        temp = [int(f_v) for f_v in frequency.values()]
        if len(temp) >= 10:
            temp.sort(reverse=True)
            threshold = temp[9]
        else: 
            threshold = 2
        tags = [f_k for f_k, f_v in frequency.items() if f_v >= threshold]
        
        book_tag[k] = tags
        n_tag += 1

    logger.info('save tag in DB -- {}'.format(n_tag))
    return book_tag
     
    
def save_to_Book(book_info, logger):
    """Save the given {book name_author: {book info}} pairs
    
    :param book_info: {book name_author: {book info}} pairs
    :type book_info: dict
    :param logger: logger instance
    :type logger: logging.Logger
    """
    get_book = len(book_info.keys())
    logger.info('[save_to_Book] get book info -- {}'.format(get_book))

    save_book = 0
    skip_book = 0
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
            
           # book_id = col_book.find_one({"name": name, "author": author})
           # col_tag.insert_one({"Book": book_id, "tags": ["tags"]})
           # logger.info('[Book: {}, author: {}] add in Book Collection'.format(name, author))
            save_book += 1
        else:
           # logger.info('[Book: {}, author: {}] already exist, so skipped'.format(name, author))
            skip_book += 1
    logger.info('DB save -- {}, skip -- {}'.format(save_book, skip_book))

def save_to_Tag(tag_data, logger):
    
    for book, tags in tag_data.items():
        name, author = book.split('_')
        
        if not name or not author: return False
        
        doc_book = col_book.find_one({"name": name, "author": author})
        doc_tag = col_tag.find_one({"Book": doc_book['_id']})
        
        if not doc_tag:
            col_tag.insert_one({"Book": doc_book['_id'], "tags": tags})
        
            logger.info('[Book: {}, Tag {}개] in Tag Collection'.format(doc_book['_id'], len(tags)))
        else:
            col_tag.update_one({"Book": doc_book['_id']},
                    {"$set": 
                        {"tags": tags}
                        })
            #logger.info('[Book: {}] already exist, so skipped'.format(doc_book['_id']))
            logger.info('[Book: {}, Tag: {}개] Update'.format(doc_book['_id'], len(tags)))

def show_DB(logger, limit=10):
    """Show book info data in Book Collection.
    
    :param logger: logger instance
    :type logger: logging.Logger
    :param limit: maximum # of items to show (default 10)
    :type limit: int
    """
    for i, b in enumerate(col_tag.find({})):
        if i == limit:
            break
        logger.info('Tag: {} -{}'.format(b['Book'], b['tags']))
