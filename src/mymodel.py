import pymongo
from pymongo import MongoClient
from src import mylogger, myconfig
import numpy as np
import pdb
import os

class model1:
    """Model for service 1 (recommend book <-- Calculate Jaccard similarity)
    """
    def compute_similarity(self, data, logger, N=5):
        """Compute Jaccard Similarity values between books and get ranked list of the most similar books

        :param data: dictionary of book tags {book id: [tag1, tag2, ...]}
        :type data: dict
        :param logger: logger instance
        :type logger: logging.Logger
        :param N: # of saving similar book (default 5)
        :type N: int
        :return: dictionary of book tags Top5 {book_id: [(similar book_id, score, [same tag list]), ...]}
        :rtype: dict
        """
        # compute similarity & save 5 similar book
        total_sim = {}
        book_ids = list(data.keys())
        for i in range(0, len(book_ids)):
            tag1 = list(data.values())[i]
            sim_score = []
            for ii in range(len(book_ids)):
                if i == ii:
                    continue
                tag2 = list(data.values())[ii]
                if len(tag1) == 0 | len(tag2) == 0:
                    continue

                # compute jaccard similarity
                intersection = list(set(tag1).intersection(set(tag2)))
                union = (len(tag1) + len(tag2)) - len(intersection)
                if len(intersection) == 0:
                    continue

                score = float(len(intersection) / union)
                
                logger.info('{}-{}: {}'.format(tag1, tag2, intersection))

                sim_score.append((book_ids[ii], score, intersection))

            sim_score.sort(key = lambda x: -x[1])
            total_sim[book_ids[i]] = sim_score[0:N]
        return total_sim


def run_model1(logger, N=5):
    """Run model 1 -- save to RecommendList Collection
        
    :param data: dict of simiar book & tag {'book_id': [('sim_book_id', score, [tags]), ... ]}
    :type data: dict
    :param logger: logger instance
    :type logger: logging.Logger
    :param N: # of saving similar book
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
    col_recommend = db[cfg['db']['col_recommend']]
    
    #prepare data & preprocesse
    doc_tags = col_tag.find()
    input_data = {}
    for doc_tag in doc_tags:
        input_data[doc_tag['Book']] = doc_tag['tags']
    
    # run model1
    m1 = model1()
    data = m1.compute_similarity(input_data, logger)
    
    for book_id, value in data.items():
        doc_recommend = col_recommend.find_one({"Book": book_id})
        if not doc_recommend:
            col_recommend.insert_one(
            {"Book": book_id, "similar_list": []})
            logger.info('Book Id: {} -- Start adding similar book'.format(book_id))
            for sim_book_id, score, tags in value:
                col_recommend.update_one(
                        {"Book": book_id},
                        {"$push": {"similar_list": {
                            "book": sim_book_id,
                            "score": score, "tags": tags}}})
                logger.info('new similar book {}, score: {}'.format(sim_book_id, score))
        '''
        else:
            logger.info('Book Id: {} -- Start changing similar book'.format(book_id))
            for sim_book_id, score, tags in value:
                col_recommend.update_one(
                {"Book": book_id},
                {"$set": { "similar_list": {"book": sim_book_id, "score": score, "tags": tags}}
                }
             )
                logger.info('new similar book {}, score: {}'.format(book_id, sim_book_id, score))
        '''
    db_client.close()

