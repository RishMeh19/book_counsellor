from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from myapp.constants import VERIFY_TOKEN, PAGE_ACCESS_TOKEN, q_dict
from myapp.search import fetch_results, index_request_in_percolator
from myapp.utility import callSendAPI, get_sender_name, postback_template, postback_template_type, one_time_not_template
import json
import redis
import inspect
import time
import sys, traceback

r = redis.Redis(host='localhost', port=6379, db=0)

@csrf_exempt
def webhook(request):
  try:
    res = {}
    sender_psid = ''
    if request.method == 'POST':
        body = json.loads(request.body)
        if (body['object'] == 'page'):
            for entry in body['entry']:
                if entry.get('changes'):
                  return
                else:  
                  webhook_event = entry['messaging'][0]
                  sender_psid = webhook_event['sender']['id']
                  if r.exists(sender_psid) and int(r.hget(sender_psid,'processing')):
                      callSendAPI(sender_psid, {"text" : 'Wait while we process'})
                  if webhook_event.get('optin'):
                    handle_quick_reply_postback(sender_psid, webhook_event['optin'])
                  elif webhook_event.get('message'):
                    if webhook_event.get('message').get('quick_reply'):
                      handle_quick_reply_postback(sender_psid, webhook_event['message']['quick_reply'])
                    else:
                      handle_message(sender_psid, webhook_event['message'])
                  res['status'] = 200
                  res['msg'] = 'event received'
                  return HttpResponse(json.dumps(res))
        else:
            return HttpResponseNotFound(status = 404)
    else:
        params = request.GET
        mode = params.get('hub.mode')
        token =  params.get('hub.verify_token')
        challenge = params.get('hub.challenge')
        if mode and token:
            if mode=='subscribe' and token == VERIFY_TOKEN:
                res = challenge
            else:
                res['status'] = 403
        return HttpResponse(res)
  except Exception as e:
    print(str(e))
    traceback.print_exc(file=sys.stdout)
    if r.exists(sender_psid):
      r.delete(sender_psid)
    if sender_psid:
      callSendAPI(sender_psid, {"text": "Sorry, Can't serve you at present, will try our best to serve you soon and suggest you your perfect book-match"})
    return HttpResponseNotFound(status = 404)


def handle_message(sender_psid, received_message, storage=True):
  response = {}
  if not r.exists(sender_psid):
      sender_name = get_sender_name(sender_psid)
      r.hset(sender_psid,'name',sender_name)
      r.expire(sender_psid,86400)
  r.hset(sender_psid,'processing',1)
  last_rep = r.hget(sender_psid,'last_rep')
  resp = received_message.get('text')
  if last_rep and storage: 
      last_rep = int(last_rep)
      if last_rep == 9:
        callSendAPI(sender_psid,{"text": "Nice to have a word with you. See you soon"})
        r.delete(sender_psid)
        return
      elif last_rep in [0,1,3,5,7,8] and inspect.stack()[1][3] != 'handle_quick_reply_postback': #to check we are not storing anything from postback call
        response = {"text":'please register your respnse by clcking appropriate option'}
        callSendAPI(sender_psid,response)
        if last_rep in [1,0,8]: #full quick_reply questions
          last_rep = last_rep - 1
        else:                     #text_reply questions with quick_reply used as confirmation
          last_rep = last_rep - 2 
        r.hset(sender_psid,'last_rep',last_rep)
        handle_message(sender_psid,received_message,False)
        return
      elif last_rep in [2,4,6]:
        r.hset(sender_psid,'last_resp',resp)
        response = postback_template('You have entered %s, should we proceed' %resp)
        r.hset(sender_psid,'last_rep',last_rep+1)
        callSendAPI(sender_psid, response)
        return
      field = q_dict[last_rep][1]
      if field:
          if resp:
            if resp.lower() != 'no':
              r.hset(sender_psid,field,resp)
  elif not last_rep:
      last_rep = -1
  last_rep = int(last_rep)+1
  r.hset(sender_psid,'last_rep',last_rep)
  if last_rep == 0:
    response = {"text":'Hi %s, we are here to suggest you your perfect book matches, for that you just have to answer some of your interest questions.'% r.hget(sender_psid,'name').decode('utf-8')}
    callSendAPI(sender_psid,response)
    response = postback_template('Are you ready')
  elif last_rep == 1:
    response = postback_template_type('Type of book you prefer')
  elif last_rep == 8:
    result = fetch_results(sender_psid) #{"text":"result"} actual result
    count = result.get('count')
    if count == 0:
      callSendAPI(sender_psid, {"text": "Sorry, we can't find any recommendation(s) for you"})
      handle_message(sender_psid, {"text":''}, storage=False)
      return
    callSendAPI(sender_psid, {"text": "We have got %s recommendation(s) for you" %str(count)})
    co_ = 1
    disp = ''
    for d in result.get('search_results'):
      disp = disp + str(co_) + ". %s by %s, %s" %( " ".join([word.capitalize() for word in d.get('name').split(" ")]), " ".join([word.capitalize() for word in d.get('author').split(" ")]), " ".join([word.capitalize() for word in d.get('genre').split(" ")])) + "\n \n"
      co_ = co_+1
    callSendAPI(sender_psid, {"text": disp})
    time.sleep(2)
    response = postback_template("Are you happy with our suggestions")#yes - delete redis key, no one_time notification postback  
  elif last_rep == 9:
    callSendAPI(sender_psid, {"text": "Would you like to receive suggestion Notification about your query, if yes, press Notify Me, else type 'no'"})
    response = one_time_not_template()
  else:
    ques = q_dict[last_rep][0]
    response = {"text" : ques} 
  callSendAPI(sender_psid, response)



def handle_quick_reply_postback(sender_psid, received_postback):
  if not r.exists(sender_psid, 'last_rep'):
    handle_message(sender_psid, {})
    return
  last_rep = int(r.hget(sender_psid,'last_rep'))
  payload = received_postback.get('payload')
  if payload == 'yes':
    if last_rep in [3,5,7]:
      resp = r.hget(sender_psid,'last_resp').decode('utf-8')
      handle_message(sender_psid,{"text":resp})
    elif last_rep in [8,9]:
      if last_rep == 9:
        index_request_in_percolator(sender_psid, received_postback.get('one_time_notif_token'))
        callSendAPI(sender_psid,{"text":"Your request has been registered with us, we will try our best to suggest you your book match"})   
      callSendAPI(sender_psid,{"text":"Thanks!! Would like to serve you again"})
      r.delete(sender_psid)
      return
    elif last_rep == 0:
      handle_message(sender_psid,{"text":''})
  elif payload == 'no':
    if last_rep in [3,5,7]:
      r.hset(sender_psid,'last_rep',last_rep-2)
      handle_message(sender_psid,{"text":''}, storage=False)
    elif last_rep == 8:
      handle_message(sender_psid,{"text":''})
    elif last_rep == 0:
        callSendAPI(sender_psid,{"text": "Nice to have a word with you. See you soon"})
        r.delete(sender_psid)
  elif payload == 'fiction':
      handle_message(sender_psid, {"text":"fiction"})
  elif payload == 'non-fiction':
      handle_message(sender_psid, {"text":"non-fiction"})
  elif payload == 'both':
      handle_message(sender_psid, {"text":"both"})






