import redis
import json
from elasticsearch import Elasticsearch
from myapp.utility import callSendAPI, send_notification

es = Elasticsearch(host= 'localhost', port=9200)
r = redis.Redis(host='localhost', port=6379, db=0)

def fetch_results(sender_psid):
    dic = fetch_params(sender_psid)
    result = search_on(dic, sender_psid)
    res = {}
    res['count'] = result['hits']['total']['value']
    res['search_results'] = []
    for hit in result['hits']['hits']:
        dic = {}
        dic['name'] = hit['_source']['name']
        dic['author'] = hit['_source']['author']
        dic['genre'] = hit['_source']['genres']
        res['search_results'].append(dic)
    return res


def fetch_params(sender_psid):
    dic = {}
    typo = r.hget(sender_psid,'typo').decode('utf-8')
    genres = r.hget(sender_psid,'genres')
    age = r.hget(sender_psid,'age')
    author = r.hget(sender_psid,'author')
    if typo == 'fiction':
        dic['typo'] = [1]
    elif typo == 'non-fiction':
        dic['typo'] = [2]
    else:
        dic['typo'] = [1,2]
    if genres:
        genres = genres.decode('utf-8')
        if genres != 'no':
            dic['genres'] = genres.lower()
    if age:
        age = age.decode('utf-8')
        if age.isdigit():
            age = int(age)
            if age <= 8:
                dic['age'] = 1
            elif age > 8 and age <= 15:
                dic['age'] = 2
            elif age > 15 and  age <= 40:
                dic['age'] = 3
            elif age >= 40 and age <= 65:
                dic['age'] = 4
            else:
                dic['age'] = 5
    if author:
        author = author.decode('utf-8')
        if author != 'no':
            dic['author'] = author.lower()
    return dic


def search_on(dic, sender_psid):
    must = []
    author = dic.get('author')
    if author:
        must.append({"match":{"author":{"query":author}}})
    genres = dic.get('genres')
    if genres:
        must.append({"match":{"genres":{"query":genres}}})
    filters = []
    typo = dic.get('typo')
    filters.append({"terms":{"typo" : typo}})
    age = dic.get('age')
    if age:
        filters.append({"term":{"age" : age}})
    body = {"query": {
                "bool":{
                    "must":must,
                    "filter":filters
                        }
                    },
                "size": 10000
                }
    r.hset(sender_psid, 'query', json.dumps(body))
    res = es.search(index="books-index", body= body)
    return res 


def index_request_in_percolator(sender_psid, notification_token):
    query = r.hget(sender_psid,'query').decode('utf-8')
    query = json.loads(query)
    body = {}
    body['query'] = query['query']
    body['sender_psid'] = sender_psid
    body['notification_token'] = notification_token
    res = es.index(index= 'requests-index', body= body)


def index_book(dic):
    notify_dic  = {}
    notify_query_set = set()
    percolate_query = {
    "query" : {
        "percolate" : {
            "field" : "query",
            "document" : ''
        }
    }
}
    for i in dic:
        res = es.index(index= 'books-index', body= i)
        percolate_query['query']['percolate']['document'] = i
        res = es.search(index= 'requests-index', body = percolate_query)
        for hit in res['hits']['hits']:
            notify_query_set.add(hit['_id'])
            not_token = hit['_source']['notification_token']
            if notify_dic.get(not_token):
                notify_dic[not_token].append({'name': i.get('name'), 'author': i.get('author')})
            else:
                notify_dic[not_token] = [{'name': i.get('name'), 'author': i.get('author'), 'genre': i.get('genres')}]
    for s in notify_query_set:
        es.delete(index = 'requests-index', id = s)
    send_notification(notify_dic)

