import sys
import os
import pdb

def test_logger(project_path=""):
    """Test logger.

    :param project_path: projecct root path
    :type project_path: str
    :return: test result.
    :rtypt: bool
    """
    from src import mylogger
    try:
        if not project_path:
            project_path='/home/ubuntu/DataArchitecture/'
        m = mylogger.get_logger('test', '{}/log'.format(project_path)
        m.debug('hi, debug')
    except Exception as e:
        print(e)
        return False
    return m

def test_config(project_path=""):
    """Test config.

    :param project_path: project root path
    :type project_path: str
    :return: test result
    :rtype: bool
    """
    from src import myconfig
    try:
        if not project_path:
            project_path = os.getenv("RECOMMEND_SERVER")
        m = myconfig.get_config('{}/share/test.config'.format(project_path)
        print('key1=', m['general'].get('key1'))
        print('key2=', m['general'].get('key2'))
        print('key3=', m['general'].get('key3'))
    except Exception as e:
        print(e)
        return False
    return True

from src import data_collect
def test_data_collection(logger):
    collected_data = data_collect.crawl_book(logger, startPage=1, endPage=1)
    logger.info('Total -- {} data collected.'.format(len(collected_data)))
    
    tag_data = data_collect.create_tag(collected_data, logger)

    if not collected_data:
        return False
    if not tag_data:
        return False
    
    data_collect.save_to_Book(collected_data, logger)
    data_collect.save_to_Tag(tag_data, logger)    
    
    return True

from src import mymodel
def test_model(logger):
    mymodel.run_model(logger)
    logger.info('Finish inserting similar book') 


if __name__ == '__main__':
    target_step = []
    if len(sys.argv) >= 2:
        target_step = sys.argv[1].split(',')
    if len(sys.argv) >= 3:
        project_path = sys.argv[2]
    else:
        project_path = ""
    print('Test steps = ', target_step)
    
    logger = test_logger(project_path)
    if not logger:
        raise Exception('Error when test_logger')
    print('Success - test_logger')

    if not target_step or 'config' in target_step:
        ret = test_config(project_path)
        if not ret:
            raise Exception('Error when test_config')
        print('Success - test_login')

    if not target_step or 'data' in target_step:
        ret = test_data_collection(logger)
        if not ret:
            raise Exception('Error when test_data_collection')
        print('Success - test_collection')
        
    if not target_step or 'model' in target_step:
        test_model(logger)
        print('Success - test_model')    
    
    print('Test completed.')
