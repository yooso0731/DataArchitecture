import sys
import os
import pdb

def test_logger():
    """Test logger.
    :return: test result.
    :rtypt: bool
    """
    from src import mylogger
    try:
        m = mylogger.get_logger('test', '/home/ubuntu/DataArchitecture/log')
        m.debug('hi, debug')
    except Exception as e:
        print(e)
        return False
    return m

def test_config():
    """Test config.
    :return: test result
    :rtype: bool
    """
    from src import myconfig
    try:
        m = myconfig.get_config('/home/ubuntu/DataArchitecture/share/test.config')
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
    print('Test steps = ', target_step)
    
    logger = test_logger()
    if not logger:
        raise Exception('Error when test_logger')
    print('Success - test_logger')

    if not target_step or 'config' in target_step:
        ret = test_confit()
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
    
    '''
    if not target_step or 'show' in target_step:
        show_DB(logger)
        print('Success - test_showDB')
    '''


    print('Test completed.')
