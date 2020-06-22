import requests
import redis
import json
from myapp.constants import PAGE_ACCESS_TOKEN

r = redis.Redis(host='localhost', port=6379, db=0)

def callSendAPI(sender_psid, response, url="https://graph.facebook.com/v2.6/me/messages", id_="id"):
  #response.update({'recipient': sender_psid})
  request_body = json.dumps({
      "recipient": {
      id_: sender_psid
      },
      "message": response
  })
  params = {'access_token':PAGE_ACCESS_TOKEN}
  headers = {
  'Content-Type': 'application/json',
  }
  res = requests.post(url = url, data = request_body, headers = headers, params=params)
  r.hset(sender_psid,'processing',0)


def get_sender_name(sender_psid):
  url = "https://graph.facebook.com/"+sender_psid
  params = {'fields':'name', 'access_token': PAGE_ACCESS_TOKEN}
  res = requests.get(url = url, params = params) 
  return res.json().get('name')



def postback_template(title):
  return(
    {
    "text": title,
    "quick_replies":[
    {
      "content_type":"text",
      "title":"Yes!",
      "payload":"yes"
    },{
      "content_type":"text",
      "title":"No!",
      "payload":"no"
        }
  ]
}
)


def postback_template_type(title):
    return (
      {
    "text": title,
    "quick_replies":[
    {
      "content_type":"text",
      "title":"Fiction",
      "payload":"fiction"
    },{
      "content_type":"text",
      "title":"Non-Fiction",
      "payload":"non-fiction"
        },
      {
      "content_type":"text",
      "title":"Both",
      "payload":"both"
        }
  ]
}
)


def one_time_not_template():
  return({
    "attachment": {
      "type":"template",
      "payload": {
        "template_type":"one_time_notif_req",
        "title":'Get notification when we find a book that matches your query',
        "payload":"yes"
      }
    }
  })


def send_notification(notify_dic):
    for i in notify_dic:
        not_id = i
        msg = 'Hi, we have %s recommendation(s) for you \n' %len(notify_dic[i])
        co_ = 1
        for m in notify_dic[i]:
            msg = msg + str(co_) +  ". " + (" ".join([word.capitalize() for word in m.get('name',"").split(" ")])) + ' by ' + (" ".join([word.capitalize() for word in m.get('author',"").split(" ")])) + ', Genre - ' + (" ".join([word.capitalize() for word in m.get('genre',"").split(" ")])) + "\n \n"
            co_ = co_ + 1
        callSendAPI(not_id, {"text": msg}, url="https://graph.facebook.com/v7.0/me/messages", id_="one_time_notif_token")
