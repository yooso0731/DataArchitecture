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
    del_pattern = "\[.*\]|\(.*\)|\s-\s.*" # delete pattern in book name(title)
    
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
                if not book_list[index].text:
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

'''
def create_tag(book_info, logger, using='mecab'):
    """Create tags using 'intro'+'p_review' of crawl_book() output 
    
    :param book_info: pairs of {'book name_author': {"p_date": "...", "intro": "...", "p_review": "..."}}
    :type book_info: dict
    :param logger: logger instance
    :type logger: logging.Logger
    :param using: use konlpy.tag name, choice=['mecab', 'hannanum', 'okt']
    :type using: str 
    :return: pairs of {"book name_author": ["tag1", "tag2", ...]}
    :rtype: dict
    """  
    logger.info('Get {} book info'.format(len(book_info.keys())))
    book_tag = {}

    if using == 'mecab':
        using = Mecab()
    elif using == 'hannanum':
        using = Hannanum()
    else:
        using = Okt()
    
    n_book = 0
    for k, v in book_info.items():
        book_info = v['intro'] + v['p_review']
        
        # extract korean
        cleans = re.sub('[^가-힣 ]', ' ', str(book_info))
        # extract nouns
        data_nouns = using.nouns(cleans)  
        
        frequency = collections.Counter(data_nouns)
        # extract tags
        temp = [int(f_v) for f_v in frequency.values()]
        if len(temp) >= 10:
            temp.sort(reverse=True)
            threshold = temp[9]
        else: 
            threshold = 2
        tags = [f_k for f_k, f_v in frequency.items() if f_v >= threshold]
        
        book_tag[k] = tags
        n_book += 1

    logger.info('Create tags of {} books'.format(n_book))
    return book_tag
'''
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer

class GraphMatrix():
    def __init__(self):
        self.tfidf = TfidfVectorizer()
        self.cnt_vec = CountVectorizer()
        self.graph_sentence = []

    def build_words_graph(self, sentence):
        cnt_vec_mat = normalize(self.cnt_vec.fit_transform(sentence).toarray().astype(float), axis=0)
        vocab = self.cnt_vec.vocabulary_
        return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word]: word for word in vocab}

class Rank():
    def get_ranks(self, graph, d=0.85):
        A = graph
        matrix_size = A.shape[0]
        # tf-idf
        for id in range(matrix_size):
            A[id, id] = 0
            link_sum = np.sum(A[:, id])
            if link_sum != 0:
                A[:, id] /= link_sum
            A[:, id] *= -d
            A[id, id] = 1

        B = (1-d) * np.ones((matrix_size, 1))
        ranks = np.linalg.solve(A, B)
        return {idx: r[0] for idx, r in enumerate(ranks)}


class TextRank():
    def __init__(self, text):
        # text: 명사 추출 끝난 문장 (list of str type)
        self.nouns = text
        self.graph_matrix = GraphMatrix()
        self.words_graph, self.idx2word = self.graph_matrix.build_words_graph(
            self.nouns)

    def keywords(self, word_num=10):
        rank = Rank()
        rank_idx = rank.get_ranks(self.words_graph)  # rank_idx == index : rank
        sorted_rank_idx = sorted(
            rank_idx, key=lambda k: rank_idx[k], reverse=True)

        keywords = {}
        index = []
        for idx in sorted_rank_idx[:word_num]:
            index.append(idx)

        for idx in index:
            keywords[self.idx2word[idx]] = rank_idx[idx]

        return keywords

def create_tag(book_info, logger, using='mecab', N=15):
    stopwords = ['소설', '소설가', '문학', '평론가']
    book_tag = {}
    if using == 'mecab': using = Mecab()
    elif using == 'hannanum': using = Hannanum()
    else: using = Okt()

    n_book = 0
    for k, v in book_info.items():
        info_sentence = []
        book_info = v['intro'] + v['p_review']

        #stopwords
        for word in stopwords:
            book_info = re.sub(word, '', book_info)

        sentences = book_info.split('.')
        [info_sentence.append(s.strip()) for s in sentences if s]

        for i in range(len(info_sentence)):
            # cleansing
            clean = re.sub('[^가-힣 ]', ' ', str(info_sentence[i]))
            info_sentence[i] = ' '.join(using.nouns(clean))
        
        try:
            textrank = TextRank(info_sentence)
            tags = [(tag, round(score, 3)) for tag, score in TextRank(info_sentence).keywords(N).items()]
        
            book_tag[k] = tags
            n_book += 1
        except:
            tags = 'None tags'
        logger.info('{}-- tags: {}'.format(k, tags))
        
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
            logger.info('[Book: {}, author: {}] add in Book Collection'.format(name, author))
        else:
            logger.info('[Book: {}, author: {}] already exist, so skipped'.format(name, author))

                
def save_to_Tag(tag_data, logger):
    """Save the given book tags in Tag Collection
    
    :param book_info: {book name_author: [tags]} pairs
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
            logger.info('[Book: {}, {} tags] in Tag Collection'.format(doc_book['_id'], len(tags)))
        else:
            col_tag.update_one({"Book": doc_book['_id']},
                    {"$set": 
                        {"tags": tags}
                        })
            logger.info('[Book: {}, {} tags] Update'.format(doc_book['_id'], len(tags)))

'''                
def show_DB(logger, limit=5):
    """Show book data in Book and Tag Collection.
    
    :param logger: logger instance
    :type logger: logging.Logger
    :param limit: maximum # of items to show (default 10)
    :type limit: int
    """
    for i, b in enumerate(col_book.find({})):
        if i == limit:
            break
        logger.info(b)
        #tags = col_tag.find_one({"Book": b["_id"]})["tags"]
        #logger.info('Book: {}, author: {}, tags: {}'.format(b['name'], b['author'], tags))
   
'''
