# DataArchitecture

- 환경변수 설정
```
vi ~/.bashrc file   
i (edit mode)

export RECOMMEND_SERVER=~/DataArchitecture
export PYTHONPATH=$PATHONPATH:$RECOMMEND_SERVER

ESC
:wq! # 저장 후 종료
```

- [Project summary](#recommed-book)

  - [Purpose](#purpose)

  - [Requirements](#requirements)

  - [How to install](#how-to-install)

- [How to use](#how-to-use)

- [Version History](#version-history)

- [Contacts](#contacts)

- [License](#license)

---

### Project summary
- 웹페이지 소개   
사용자에게 도서명, 저자를 입력받은 후 그와 유사한 주제의 도서를 추천해주는 홈페이지
   
- 사용 데이터 출처
YES24 페이지 내 국내-소설/시/희곡 분야 베스트셀러     
<도서명, 저자, 출판일, 소개글, 출판사 서평문> 크롤링
(http://www.yes24.com/24/Category/Display/001001046)   
    
- 진행 프레임워크
1. (베스트셀러/신작) 데이터 수집
2. 형태소 분석, 빈도 분석을 이용하여 도서별 주제 태그 생성
3. 도서간 자카드 유사도 계산
4. 사용자에게 입력받은 도서와 유사한 도서 TopN개 출력

#### Purpose

데이터아키텍처창의설계 수업 프로젝트 - server side

#### Requirements

* python >= 3.7.7

* flask >= 1.1.1

* mongoDB >= 3.6.3

* sphinx >= 3.5.3 

* konlpy

#### How to install

* konlpy: 운영체제에 맞게 공식 페이지 내용 참고해서 진행하기를 권장함    
(https://konlpy-ko.readthedocs.io/ko/v0.4.3/install/)   
만약 ubuntu 운영체제라면 Mecab 설치까지 진행

* project clone
```sh

git clone ...........

cd da_design_server20171482

pip3 install -r requirements.txt

```

---

### How to use

TODO

---

### Version History

* v.1.0.0 : 개발중

---

### Contacts

yoosomail@gmail.com

---

### License

Apache-2.0


