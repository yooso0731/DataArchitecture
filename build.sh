#!/bin/bash
SHELL_PATH=`pwd -P`
echo $SHELL_PATH
export RECOMMEND_SERVER=$SHELL_PATH
python3 ./test.py config $SHELL_PATH
