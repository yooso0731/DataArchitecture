#-*- coding: utf-8 -*-
if [ $# -lt 1 ]; then
	echo 'give 1 argument'
else
	if [ $1 = 'recommend' ]; then
		echo "recommend"
		curl -H "Content-type: application/json" -X POST -d '{"book_name":"달러구트 꿈 백화점", "author":"이미예"}' http://127.0.0.1:11100/recommend >> ret
	elif [ $1 = 'tag' ]; then
		curl -H "Content-type: application/json" -X POST -d '{"book_name":"달러구트 꿈 백화점", "author":"이미예"}' http://127.0.0.1:11100/tag >> ret
	fi
fi
