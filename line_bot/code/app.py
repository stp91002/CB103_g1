#!/usr/bin/python
#coding:utf-8

#tensorflow
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf


from flask import Flask, request, abort,render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, FollowEvent, JoinEvent,PostbackEvent,
    TextSendMessage, TemplateSendMessage,ImagemapSendMessage,
    BaseSize,URIImagemapAction,ImagemapArea, MessageImagemapAction,
    TextMessage, ImageMessage, ButtonsTemplate,
    PostbackTemplateAction, MessageTemplateAction,PostbackAction,
    URITemplateAction,ImageSendMessage,CarouselTemplate,CarouselColumn,URIAction,
    CameraAction, CameraRollAction,QuickReply, QuickReplyButton,ConfirmTemplate
)



try:
    from urllib.parse import urlparse,parse_qs
except ImportError:
    from urlparse import urlparse,parse_qs



import json

import requests


import os
ip_location='localhost'


#要設定成global的參數
next_menu_id = None
sell_data = None
buy_data = None
order_data = None

#自訂參數
transaction_list=["番茄","香蕉","橘子","高麗菜","玉米"]

#交易清單物件

#生產者掛賣
class product_sell(object):
    """docstring for menu"""
    def __init__(user,product,price=None,amount=None):
        user.product = product
        user.price = price
        user.amount = amount

#個人&公司直買
class product_buy(object):
    """docstring for menu"""
    def __init__(user,product,product_id,price,amount=None):
        user.product = product
        user.product_id = product_id
        user.price = price
        user.amount = amount

#公司團體掛單
class order_up(object):
    """docstring for menu"""
    def __init__(user,product,price=None,amount=None):
        user.product = product
        user.price = price
        user.amount = amount


#tensorflow function
def load_graph(model_file):
  graph = tf.Graph()
  graph_def = tf.GraphDef()

  with open(model_file, "rb") as f:
    graph_def.ParseFromString(f.read())
  with graph.as_default():
    tf.import_graph_def(graph_def)

  return graph

def read_tensor_from_image_file(file_name,
                                input_height=299,
                                input_width=299,
                                input_mean=0,
                                input_std=255):
  input_name = "file_reader"
  output_name = "normalized"
  file_reader = tf.read_file(file_name, input_name)
  if file_name.endswith(".png"):
    image_reader = tf.image.decode_png(
        file_reader, channels=3, name="png_reader")
  elif file_name.endswith(".gif"):
    image_reader = tf.squeeze(
        tf.image.decode_gif(file_reader, name="gif_reader"))
  elif file_name.endswith(".bmp"):
    image_reader = tf.image.decode_bmp(file_reader, name="bmp_reader")
  else:
    image_reader = tf.image.decode_jpeg(
        file_reader, channels=3, name="jpeg_reader")
  float_caster = tf.cast(image_reader, tf.float32)
  dims_expander = tf.expand_dims(float_caster, 0)
  resized = tf.image.resize_bilinear(dims_expander, [input_height, input_width])
  normalized = tf.divide(tf.subtract(resized, [input_mean]), [input_std])
  sess = tf.Session()
  result = sess.run(normalized)

  return result

def load_labels(label_file):
  label = []
  proto_as_ascii_lines = tf.gfile.GFile(label_file).readlines()
  for l in proto_as_ascii_lines:
    label.append(l.rstrip())
  return label



secretFile=json.load(open("./line_key",'r'))

app = Flask(__name__)


line_bot_api = LineBotApi(secretFile.get("channel_access_token"))

handler = WebhookHandler(secretFile.get("secret_key"))

server_url = secretFile.get("server_url")

# 啟動server對外接口，使Line能丟消息進來
@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

#製作一個測試用接口
@app.route('/hello',methods=['GET'])
def hello():
    return 'Hello World!!'

@app.route('/feedback')
def quality():
    html = """<html><head><title>品質回饋</title></head><body><p>回饋內容</p><form method="POST"><input name="text"><input type="submit"></form><p></p><p></p><p>回饋紀錄</p>"""

    #取出所有回饋
    Endpoint='http://%s:5001/feedback_list' % (ip_location)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    feedback_list = Response.json()

    for p in feedback_list:
        html = html+"<pre>回饋編號{}  時間{}/{}/{}</pre><pre>內容:{}</pre>".format(p[0],p[1],p[2],p[3],p[4])
    html = html+"</body></html>"

    return html

@app.route('/feedback',methods=['POST'])
def quality_post():
    #接收提交的資料
    text = request.form['text']
    processed_text = text.upper()

    # html = """<html><head><title>品質回饋</title></head><body><p>回饋內容</p><form method="POST"><input name="text"><input type="submit"></form><p></p><p></p><p>回饋紀錄</p>"""
    # #取出所有回饋
    # Endpoint='http://%s:5001/feedback_list' % (ip_location)
    # Header={'Content-Type':'application/json'}
    # Response=requests.get(Endpoint,headers=Header)    
    # print(Response)
    # print(Response.text)

    # feedback_list = Response.json()

    # for p in feedback_list:
    #     html = html+"<pre>回饋編號{}  時間{}/{}/{}</pre><pre>內容:{}</pre>".format(p[0],p[1],p[2],p[3],p[4])
    # html = html+"</body></html>"

    if (processed_text==""):
        pass
    else:
        #回饋存入mysql
        feedback_info = {  
            "content": processed_text,
        }

        Endpoint='http://%s:5001/feedback' % (ip_location)
        Header={'Content-Type':'application/json'}
        Response=requests.post(Endpoint,headers=Header,data=json.dumps(feedback_info))

        print(Response)
        print(Response.text)

    return "回饋收到了！"


@app.route('/question')
def home():
    html = """<html><head><title>問題回報</title></head><body><p>問題內容</p><form method="POST"><input name="text"><input type="submit"></form><p></p><p></p><p>問題紀錄</p>"""

    #取出所有回饋
    Endpoint='http://%s:5001/question_list' % (ip_location)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    question_list = Response.json()

    for p in question_list:
        html = html+"<pre>問題編號{}  時間{}/{}/{}</pre><pre>內容:{}</pre>".format(p[0],p[1],p[2],p[3],p[4])
    html = html+"</body></html>"

    return html

@app.route('/question',methods=['POST'])
def home_post():
    #接收提交的資料
    text = request.form['text']
    processed_text = text.upper()

    # html = """<html><head><title>品質回饋</title></head><body><p>回饋內容</p><form method="POST"><input name="text"><input type="submit"></form><p></p><p></p><p>回饋紀錄</p>"""
    # #取出所有回饋
    # Endpoint='http://%s:5001/feedback_list' % (ip_location)
    # Header={'Content-Type':'application/json'}
    # Response=requests.get(Endpoint,headers=Header)    
    # print(Response)
    # print(Response.text)

    # feedback_list = Response.json()

    # for p in feedback_list:
    #     html = html+"<pre>回饋編號{}  時間{}/{}/{}</pre><pre>內容:{}</pre>".format(p[0],p[1],p[2],p[3],p[4])
    # html = html+"</body></html>"

    if (processed_text==""):
        pass
    else:
        #回饋存入mysql
        question_info = {  
            "content": processed_text,
        }

        Endpoint='http://%s:5001/question' % (ip_location)
        Header={'Content-Type':'application/json'}
        Response=requests.post(Endpoint,headers=Header,data=json.dumps(question_info))

        print(Response)
        print(Response.text)

    return "問題收到了！"


#個人及團體得到商品清單
@app.route('/read_product/<product>',methods=['GET'])
def read_product(product):

    Endpoint='http://%s:5001/get_product_lists/%s' % (ip_location,product)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_product_list = Response.json()

    html = "<html><head><title>查詢結果</title></head><body><p>查詢結果</p><p></p><p></p><pre>{:<15}{:<15}{:<15}{:<15}</pre>".format("商品編號","價格","剩餘數量","上架日期")
    for p in read_product_list:
        html = html+"<pre>{:<15}{:<15}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4],p[5])
    html = html+"</body></html>"
    return html

#個人得到交易清單
@app.route('/get_person_transaction_lists/<user_id>',methods=['GET'])
def get_person_transaction_lists(user_id):

    Endpoint='http://%s:5001/get_person_transaction_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_person_transaction_list = Response.json()

    html = "<html><head><title>查詢結果</title></head><body><p>查詢結果</p><p></p><p></p><pre>{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}</pre>".format("交易編號","商品編號","商品","價格","交易數量","交易日期")
    for p in read_person_transaction_list:
        html = html+"<pre>{:<15}{:<10}{:<10}{:<10}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7])
    html = html+"</body></html>"
    return html

#公司團體查詢訂單
@app.route('/get_order_lists/<user_id>',methods=['GET'])
def get_order_lists(user_id):

    Endpoint='http://%s:5001/get_order_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_person_transaction_list = Response.json()

    html = "<html><head><title>查詢結果</title></head><body><p>查詢結果</p><p></p><p></p><pre>{:<15}{:<15}{:<15}{:<15}{:<15}</pre>".format("訂單編號","商品","價格","數量","交易日期")
    for p in read_person_transaction_list:
        html = html+"<pre>{:<15}{:<15}{:<15}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4],p[5],p[6])
    html = html+"</body></html>"
    return html

#公司團體得到交易清單
@app.route('/get_group_transaction_lists/<user_id>',methods=['GET'])
def get_group_transaction_lists(user_id):
    #一般交易
    Endpoint='http://%s:5001/get_person_transaction_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_person_transaction_list = Response.json()

    html = "<html><head><title>查詢結果</title></head><body><p>查詢結果</p><p></p><p></p><p>一般交易</p><pre>{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}</pre>".format("交易編號","商品編號","商品","價格","交易數量","交易日期")
    for p in read_person_transaction_list:
        html = html+"<pre>{:<15}{:<10}{:<10}{:<10}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7])
    
    #訂單交易
    Endpoint='http://%s:5001/get_order_transaction_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_group_transaction_list = Response.json()

    html = html+"<p></p><p></p><p>訂單交易</p><pre>{:<10}{:<15}{:<15}</pre>".format("訂單交易編號","訂單編號","交易日期")
    for p in read_group_transaction_list:
        html = html+"<pre>{:<15}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4])

    html = html+"</body></html>"
    return html

#生產者查看商品清單
@app.route('/read_product_lists/<user_id>',methods=['GET'])
def read_product_lists(user_id):

    Endpoint='http://%s:5001/read_product_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_product_list = Response.json()

    html = "<html><head><title>查詢結果</title></head><body><p>查詢結果</p><p></p><p></p><pre>{:<15}{:<15}{:<15}{:<15}{:<15}</pre>".format("商品編號","商品","價格","剩餘數量","上架日期")
    for p in read_product_list:
        html = html+"<pre>{:<15}{:<15}{:<15}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4],p[5],p[6])
    html = html+"</body></html>"
    return html

#生產者查看訂單清單
@app.route('/read_order_lists/<user_id>',methods=['GET'])
def read_order_lists(user_id):

    Endpoint='http://%s:5001/producer_get_order_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_order_lists = Response.json()

    html = "<html><head><title>查詢結果</title></head><body><p>查詢結果</p><p></p><p></p><p>訂單交易</p><pre>{:<15}{:<15}{:<15}{:<15}{:<15}</pre>".format("訂單編號","商品","價格","數量","訂單日期")
    for p in read_order_lists:
        html = html+"<pre>{:<15}{:<15}{:<15}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4],p[5],p[6])

    html = html+"</body></html>"
    return html

#生產者得到交易清單
@app.route('/get_producer_transaction_lists/<user_id>',methods=['GET'])
def get_producer_transaction_lists(user_id):
    #一般交易
    Endpoint='http://%s:5001/get_producer_transaction_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_transaction_list = Response.json()

    html = "<html><head><title>查詢結果</title></head><body><p>查詢結果</p><p></p><p></p><p>一般交易</p><pre>{:<10}{:<10}{:<10}{:<10}{:<10}{:<10}</pre>".format("交易編號","商品編號","商品","價格","交易數量","交易日期")
    for p in read_transaction_list:
        html = html+"<pre>{:<15}{:<10}{:<10}{:<10}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7])
    
    #訂單交易
    Endpoint='http://%s:5001/get_producer_order_transaction_lists/%s' % (ip_location,user_id)
    Header={'Content-Type':'application/json'}
    Response=requests.get(Endpoint,headers=Header)    
    print(Response)
    print(Response.text)

    read_order_transaction_list = Response.json()

    html = html+"<p></p><p></p><p>訂單交易</p><pre>{:<10}{:<15}{:<15}</pre>".format("訂單交易編號","訂單編號","交易日期")
    for p in read_order_transaction_list:
        html = html+"<pre>{:<15}{:<15} {}/{}/{}</pre>".format(p[0],p[1],p[2],p[3],p[4])

    html = html+"</body></html>"
    return html

@handler.add(FollowEvent)
def reply_text_and_get_user_profile(event):

    # 取出消息內User的資料
    user_profile = line_bot_api.get_profile(event.source.user_id)
        
    # 將用戶資訊做成合適Json
    user_info = {  
        "user_id": user_profile.user_id,
        "display_name": user_profile.display_name,
        "picture_url" : user_profile.picture_url,
    }
    
    # 將json傳回API Server
    Endpoint='http://%s:5001/users' % (ip_location)
    
    # header要特別註明是json格式
    Header={'Content-Type':'application/json'}
    
    # 傳送post對API server新增資料 
    Response=requests.post(Endpoint,headers=Header,data=json.dumps(user_info))
    
    #印出Response的資料訊息
    print(Response)
    print(Response.text)

    menu_id = secretFile.get("home_page_id")

    # 取出消息內User的資料
    user_profile = line_bot_api.get_profile(event.source.user_id)
    
    # header要特別註明是json格式
    Header={'Content-Type':'application/json'}
    
    
    # 將菜單綁定在用戶身上
    # 要到Line官方server進行這像工作，這是官方的指定接口
    linkMenuEndpoint='https://api.line.me/v2/bot/user/%s/richmenu/%s' % (user_profile.user_id, menu_id)
    
    # 官方指定的header
    linkMenuRequestHeader={'Content-Type':'image/jpeg','Authorization':'Bearer %s' % secretFile["channel_access_token"]}
    
    # 傳送post method封包進行綁定菜單到用戶上
    lineLinkMenuResponse=requests.post(linkMenuEndpoint,headers=linkMenuRequestHeader)
    #推送訊息給官方Line
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="呀哈囉！\n歡迎使用 果菜on賴！\n現在是v2.0.0版本唷~" ))

@handler.add(PostbackEvent)
def handle_post_message(event):

    global next_menu_id

    #抓取postback action的data
    data = event.postback.data

    #用query string 解析data
    data=parse_qs(data)




    if (data['where']==['home_page']):

        #用於切換rich_menu
        if (data['action']==['switch']):
            # 將json傳回API Server
            Endpoint='http://%s:5001/users/%s' % (ip_location,event.source.user_id)
            
            # header要特別註明是json格式
            Header={'Content-Type':'application/json'}
            
            # 傳送post對API server新增資料 
            Response=requests.get(Endpoint,headers=Header)
            
            #印出Response的資料訊息
            print(Response)
            print(Response.text)

            user_type = Response.json()

            if (user_type[0] == 'visitor'):
                next_menu_id = secretFile.get("visitor_page_id")
            elif (user_type[0] == 'person'):
                next_menu_id = secretFile.get("person_page_id")
            elif (user_type[0] == 'group'):
                next_menu_id = secretFile.get("group_page_id")
            elif (user_type[0] == 'producer'):
                next_menu_id = secretFile.get("producer_page_id")

        elif (data['action']==['quality']):
            next_menu_id = secretFile.get("quality_page_id")
        
        # header要特別註明是json格式
        Header={'Content-Type':'application/json'}
        # 將菜單綁定在用戶身上
        # 要到Line官方server進行這像工作，這是官方的指定接口
        linkMenuEndpoint='https://api.line.me/v2/bot/user/%s/richmenu/%s' % (event.source.user_id, next_menu_id)

        # 官方指定的header
        linkMenuRequestHeader={'Content-Type':'image/jpeg','Authorization':'Bearer %s' % secretFile["channel_access_token"]}

        # 傳送post method封包進行綁定菜單到用戶上
        lineLinkMenuResponse=requests.post(linkMenuEndpoint,headers=linkMenuRequestHeader)

        next_menu_id = None

    

    if (data['where']==['quality_page']):
        if (data['action']==['upload_picture']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="使用快捷功能或自行上傳照片",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(action=CameraAction(label="立即拍照")),
                                        QuickReplyButton(action=CameraRollAction(label="上傳照片"))
                                    ]
                                )
                )
            )
        elif (data['action']==['analyze']):
            file_name = "quality/"+data['picture'][0]+".jpg"
            model_file = "model/output_graph.pb"
            label_file = "model/output_labels.txt"
            input_height = 224
            input_width = 224
            input_mean = 0
            input_std = 255
            input_layer = "Placeholder"
            output_layer = "final_result"

            graph = load_graph(model_file)
            t = read_tensor_from_image_file(
                file_name,
                input_height=input_height,
                input_width=input_width,
                input_mean=input_mean,
                input_std=input_std)

            input_name = "import/" + input_layer
            output_name = "import/" + output_layer
            input_operation = graph.get_operation_by_name(input_name)
            output_operation = graph.get_operation_by_name(output_name)

            with tf.Session(graph=graph) as sess:
              results = sess.run(output_operation.outputs[0], {
                  input_operation.outputs[0]: t
              })
            results = np.squeeze(results)

            top_k = results.argsort()[-5:][::-1]
            labels = load_labels(label_file)

            quality_text = ""
            for i in top_k:
                results[i] = results[i]*100
                results[i] = results[i].item()
                quality_text = quality_text+labels[i]+"的可能性為{0:.2f}%".format(results[i])
            quality_text = quality_text.replace("good","好").replace("soso","中間").replace("bad","壞").replace("%","%\n",2)
            
            line_bot_api.reply_message(
                          event.reply_token,
                          TextSendMessage(text=quality_text)
                      )

    if (data['where']==['visitor_page']):
        if (data['action']==['join']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇會員身分",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="個人會員", data="where=visitor_page&action=chose&is=person")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="公司會員", data="where=visitor_page&action=chose&is=group")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="生產者", data="where=visitor_page&action=chose&is=producer")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="訪客", data="where=visitor_page&action=chose&is=visitor")
                                                )
                                            ]
                                )
                )
            )


    if (data['where']==['person_page']):
        if (data['action']==['user_data']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="修改會員身分", data="where=person_page&action=alter_type")
                                                )
                                            ]
                                )
                )
            )

        elif (data['action']==['product']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="查看商品列表", data="where=person_page&action=product_list")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="購買商品", data="where=person_page&action=choose_buy")
                                                )
                                            ]
                                )
                )
            )
        elif (data['action']==['product_list']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇想查詢的商品列表",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[0], data="where=person_page&action=show_list&what=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[1], data="where=person_page&action=show_list&what=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[2], data="where=person_page&action=show_list&what=2")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[3], data="where=person_page&action=show_list&what=3")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[4], data="where=person_page&action=show_list&what=4")
                                        )
                                    ]
                                )
                )
            )

        elif (data['action']==['show_list']):

            get_url = 'https://%s/read_product/%s' % (server_url,data['what'][0])

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/5205/food-healthy-vegetables-potatoes.jpg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n商品選單"),imagemap_product_list]
            )

        elif (data['action']==['choose_buy']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入欲購買之商品編號\n輸入格式為=> 0-商品編號",
                )
            )

        elif (data['action']==['confirm']):
            if (data['as']==['no']):
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請重新選擇")
            )
            else:
                global buy_data

                buy_data = product_buy(product=data['product'][0],product_id=data['product_id'][0],price=data['price'][0])

                buy_message = "購買的商品為《%s》\n商品編號為《%s》\n商品單價為《%s》(元/台斤)\n剩餘數量為《%s》(台斤)\n" \
                                % (data['product'][0],data['product_id'][0],data['price'][0],data['amount'][0])

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=buy_message+"請輸入購買商品的編號及數量\n輸入格式為=>1-商品編號-數量")
                )

        elif (data['action']==['final_confirm']):
            if (data['as']==['no']):
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請重新選擇")
            )
            else:
                # 將用戶資訊做成合適Json
                product_info = {  
                    "product": data['product'][0],
                    "product_id": data['product_id'][0],
                    "price" : data['price'][0],
                    "amount" : data['amount'][0],
                }
                
                # 將json傳回API Server
                Endpoint='http://%s:5001/product/buy/%s' % (ip_location,event.source.user_id)
                
                # header要特別註明是json格式
                Header={'Content-Type':'application/json'}
                
                # 傳送post對API server新增資料 
                Response=requests.post(Endpoint,headers=Header,data=json.dumps(product_info))
                
                #印出Response的資料訊息
                print(Response)
                print(Response.text)

                transaction_result = Response.json()
                if (transaction_result[0] == "not_enough"):
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="購買失敗，商品剩餘數量不足")
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="購買成功~")
                    )

        elif (data['action']==['get_transaction_lists']):

            get_url = 'https://%s/get_person_transaction_lists/%s' % (server_url,event.source.user_id)

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/261621/pexels-photo-261621.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n交易清單"),imagemap_product_list]
            )

    if (data['where']==['group_page']):
        if (data['action']==['user_data']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="修改會員身分", data="where=group_page&action=alter_type")
                                                )
                                            ]
                                )
                )
            )

        elif (data['action']==['product']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="查看商品列表", data="where=group_page&action=product_list")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="購買商品", data="where=group_page&action=choose_buy")
                                                )
                                            ]
                                )
                )
            )
        elif (data['action']==['product_list']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇想查詢的商品列表",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[0], data="where=group_page&action=show_list&what=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[1], data="where=group_page&action=show_list&what=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[2], data="where=group_page&action=show_list&what=2")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[3], data="where=group_page&action=show_list&what=3")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[4], data="where=group_page&action=show_list&what=4")
                                        )
                                    ]
                                )
                )
            )

        elif (data['action']==['show_list']):

            get_url = 'https://%s/read_product/%s' % (server_url,data['what'][0])

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/5205/food-healthy-vegetables-potatoes.jpg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n商品選單"),imagemap_product_list]
            )

        elif (data['action']==['choose_buy']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入欲購買之商品編號\n輸入格式為=> 0-商品編號",
                )
            )

        elif (data['action']==['uplist']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="檢視已開訂單", data="where=group_page&action=get_order_lists")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="開新訂單", data="where=group_page&action=new_uplist")
                                                )
                                            ]
                                )
                )
            )

        elif (data['action']==['get_order_lists']):

            get_url = 'https://%s/get_order_lists/%s' % (server_url,event.source.user_id)

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/261621/pexels-photo-261621.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n我的訂單"),imagemap_product_list]
            )

        #開訂單
        elif (data['action']==['new_uplist']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇想開訂單的商品",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[0], data="where=group_page&action=up&what=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[1], data="where=group_page&action=up&what=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[2], data="where=group_page&action=up&what=2")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[3], data="where=group_page&action=up&what=3")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[4], data="where=group_page&action=up&what=4")
                                        )
                                    ]
                                )
                )
            )

        elif (data['action']==['up']):

            global order_data

            order_data = order_up(product=transaction_list[int(data['what'][0])])

            per_title = "訂單的"+transaction_list[int(data['what'][0])]+"單價(元/台斤)是？\n"
            amount_title = "訂單的"+transaction_list[int(data['what'][0])]+"數量(台斤)是？\n"
            type_title = "輸入格式為=> 2-單價-數量"
            total = per_title+amount_title+type_title
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=total)
            )

        elif (data['action']==['confirm']):
            if (data['as']==['no']):
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請重新選擇")
            )
            else:
                order_info = {  
                    "product": data['product'][0],
                    "price": data['price'][0],
                    "amount" : data['amount'][0],
                }
                
                # 將json傳回API Server
                Endpoint='http://%s:5001/order/%s' % (ip_location,event.source.user_id)
                
                # header要特別註明是json格式
                Header={'Content-Type':'application/json'}
                
                # 傳送post對API server新增資料 
                Response=requests.post(Endpoint,headers=Header,data=json.dumps(order_info))
                
                #印出Response的資料訊息
                print(Response)
                print(Response.text)

                order_data = None

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="訂單已上架")
                )

        elif (data['action']==['get_transaction_lists']):

            get_url = 'https://%s/get_group_transaction_lists/%s' % (server_url,event.source.user_id)

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/261621/pexels-photo-261621.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n交易清單"),imagemap_product_list]
            )

    if (data['where']==['producer_page']):
        if (data['action']==['user_data']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="修改會員身分", data="where=producer_page&action=alter_type")
                                                )
                                            ]
                                )
                )
            )

        elif (data['action']==['product']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="商品上架", data="where=producer_page&action=product_upload")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="拿取訂單", data="where=producer_page&action=choose_order")
                                                )
                                            ]
                                )
                )
            )

        elif (data['action']==['product_upload']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請選擇想販售的商品",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[0], data="where=producer_page&action=sell&what=0")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[1], data="where=producer_page&action=sell&what=1")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[2], data="where=producer_page&action=sell&what=2")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[3], data="where=producer_page&action=sell&what=3")
                                        ),
                                        QuickReplyButton(
                                            action=PostbackAction(label=transaction_list[4], data="where=producer_page&action=sell&what=4")
                                        )
                                    ]
                                )
                )
            )
        elif (data['action']==['sell']):

            global sell_data

            sell_data = product_sell(product=transaction_list[int(data['what'][0])])

            per_title = "販售的"+transaction_list[int(data['what'][0])]+"單價(元/台斤)是？\n"
            amount_title = "販售的"+transaction_list[int(data['what'][0])]+"數量(台斤)是？\n"
            type_title = "輸入格式為=> 數字(空白)數字"
            total = per_title+amount_title+type_title
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=total)
            )

        elif (data['action']==['confirm']):
            if (data['as']==['no']):
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請重新選擇")
            )
            else:
                product_info = {  
                    "product": data['product'][0],
                    "price": data['price'][0],
                    "amount" : data['amount'][0],
                }
                
                # 將json傳回API Server
                Endpoint='http://%s:5001/product/%s' % (ip_location,event.source.user_id)
                
                # header要特別註明是json格式
                Header={'Content-Type':'application/json'}
                
                # 傳送post對API server新增資料 
                Response=requests.post(Endpoint,headers=Header,data=json.dumps(product_info))
                
                #印出Response的資料訊息
                print(Response)
                print(Response.text)

                sell_data = None

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="商品已上架")
                )
        elif (data['action']==['choose_order']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請輸入欲拿取的訂單編號\n輸入格式為=> 3-商品編號",
                )
            )
        
        elif (data['action']==['order_confirm']):
            if (data['as']==['no']):
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請重新選擇")
            )
            else:
                order_info = {  
                    "order_id": data['order_id'][0],
                }
                
                # 將json傳回API Server
                Endpoint='http://%s:5001/order/get/%s' % (ip_location,event.source.user_id)
                
                # header要特別註明是json格式
                Header={'Content-Type':'application/json'}
                
                # 傳送post對API server新增資料 
                Response=requests.post(Endpoint,headers=Header,data=json.dumps(order_info))
                
                #印出Response的資料訊息
                print(Response)
                print(Response.text)

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="訂單已拿取~")
                )

        elif (data['action']==['product_data']):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇要使用的功能",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="查看販賣商品", data="where=producer_page&action=read_product_lists")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="查看現有訂單", data="where=producer_page&action=read_order_lists")
                                                )
                                            ]
                                )
                )
            )
        
        elif (data['action']==['read_product_lists']):

            get_url = 'https://%s/read_product_lists/%s' % (server_url,event.source.user_id)

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/5205/food-healthy-vegetables-potatoes.jpg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n我的商品"),imagemap_product_list]
            )

        elif (data['action']==['read_order_lists']):

            get_url = 'https://%s/read_order_lists/%s' % (server_url,event.source.user_id)

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/261621/pexels-photo-261621.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n訂單清單"),imagemap_product_list]
            )

        elif (data['action']==['get_transaction_lists']):

            get_url = 'https://%s/get_producer_transaction_lists/%s' % (server_url,event.source.user_id)

            imagemap_product_list = ImagemapSendMessage(
                base_url='https://images.pexels.com/photos/261621/pexels-photo-261621.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260',
                alt_text='for_product_list',
                base_size=BaseSize(height=750, width=1260),
                actions=[
                    URIImagemapAction(
                        link_uri=get_url,
                        area=ImagemapArea(
                            x=0, y=0, width=1260, height=750
                        )
                    )
                ]
            )

            line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text="請點選圖片前往~\n交易清單"),imagemap_product_list]
            )
    #回首頁
    if (data['action']==['go_home']):
  
        Header={'Content-Type':'application/json'}

        linkMenuEndpoint='https://api.line.me/v2/bot/user/%s/richmenu/%s' % (event.source.user_id, secretFile.get("home_page_id"))
    
        linkMenuRequestHeader={'Content-Type':'image/jpeg','Authorization':'Bearer %s' % secretFile["channel_access_token"]}
    
        lineLinkMenuResponse=requests.post(linkMenuEndpoint,headers=linkMenuRequestHeader)

    if (data['action']==['alter_type']):
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="選擇修改後會員身分",
                                quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=PostbackAction(label="個人會員", data="where=visitor_page&action=new&is=person")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="公司會員", data="where=visitor_page&action=new&is=group")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="生產者", data="where=visitor_page&action=new&is=producer")
                                                ),
                                                QuickReplyButton(
                                                    action=PostbackAction(label="訪客", data="where=visitor_page&action=new&is=visitor")
                                                )
                                            ]
                                )
                )
        )

    #加入時，修改會員身分

    if (data['action']==['chose']):
        
        user_info = {  
             "user_type" : data['is'][0],
        }
        
        Endpoint='http://%s:5001/users/alter/%s' % (ip_location,event.source.user_id)
            
        Header={'Content-Type':'application/json'}
            
        Response=requests.post(Endpoint,headers=Header,data=json.dumps(user_info))

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="加入成功~請回主頁~\n請重新進入會員專區")
        )

    #修改會員身分
    if (data['action']==['new']):
        
        user_info = {  
             "user_type" : data['is'][0],
        }
        
        Endpoint='http://%s:5001/users/alter/%s' % (ip_location,event.source.user_id)
            
        Header={'Content-Type':'application/json'}
            
        Response=requests.post(Endpoint,headers=Header,data=json.dumps(user_info))

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="修改成功~請回主頁~\n請重新進入會員專區")
        )

    #修改交易用資料
    #if (data['action']==['alter_true_data']):

@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):
    file_path = "quality/"+event.message.id+".jpg"

    message_content = line_bot_api.get_message_content(event.message.id)
    with open(file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="選擇要分析的果菜",
                        quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=PostbackAction(label="小番茄", data="where=quality_page&action=analyze&picture="+event.message.id)
                                        )
                                    ]
                        )
        )
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    
    #用於買賣訂單
    get_text = event.message.text

    get_list = get_text.split()

    get_list_hyphen = get_text.split("-")

    try:
        if ( type(int(get_list[0]))==int and type(int(get_list[1]))==int):

            if sell_data.price == None:
                sell_data.price=int(get_list[0])
            if sell_data.amount == None:
                sell_data.amount=int(get_list[1])

            check_text = "販售的商品是《"+sell_data.product+"》\n"\
                            +"單價為《"+str(sell_data.price)+"》(元/台斤)\n"+"數量為《"+str(sell_data.amount)+"》(台斤)"
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://images.pexels.com/photos/533360/pexels-photo-533360.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940',
                        title='確認交易資訊',
                        text=check_text,
                        actions=[
                            PostbackAction(
                                label='確認送出',
                                text='確認送出',
                                data='where=producer_page&action=confirm&as=yes&product='+sell_data.product+'&price='+str(sell_data.price)+'&amount='+str(sell_data.amount)
                            ),
                            PostbackAction(
                                label='取消',
                                text='取消',
                                data='where=producer_page&action=confirm&as=no'
                            )
                        ]
                    )
                )
            )
    except (ValueError,IndexError):
        pass

    try:
        if ( int(get_list_hyphen[0])==0 and type(int(get_list_hyphen[1]))==int):

            Endpoint='http://%s:5001/product/%s' % (ip_location,int(get_list_hyphen[1]))
            
            Header={'Content-Type':'application/json'}
            
            Response=requests.get(Endpoint,headers=Header)
            
            print(Response)
            print(Response.text)

            product_info = Response.json()

            if (product_info[0]== 'error'):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="無此商品編號，請重新確認")
                )
            if (product_info[0]== 'invisible'):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="此編號商品已售罄~\n請購買其他商品^_^")
                )
            else:
                #0 product 1 price 2 amount
                product_message = "購買的商品為《%s》\n商品單價為《%s》(元/台斤)\n商品剩餘數量為《%s》(台斤)\n" % (product_info[0],product_info[1],product_info[2])

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=product_message+"是否購買此商品",
                                    quick_reply=QuickReply(
                                                items=[
                                                    QuickReplyButton(
                                                        action=PostbackAction(label="是", data=\
                                                            "where=person_page&action=confirm&as=yes&product_id=%s&product=%s&price=%s&amount=%s" % (get_list_hyphen[1],product_info[0],product_info[1],product_info[2]))
                                                    ),
                                                    QuickReplyButton(
                                                        action=PostbackAction(label="否", data="where=person_page&action=confirm&as=no")
                                                    )
                                                ]
                                    )
                    )
                )
    except (ValueError,IndexError):
        pass


    try:
        if ( int(get_list_hyphen[0])==1 and type(int(get_list_hyphen[1]))==int and type(int(get_list_hyphen[2]))==int):

            if buy_data.amount == None:
                buy_data.amount=int(get_list_hyphen[2])

            check_text = "販售的商品是《"+buy_data.product+"》編號是《"+buy_data.product_id+"》\n"\
                            +"單價為《"+str(buy_data.price)+"》(元/台斤)\n"+"購買數量為《"+str(buy_data.amount)+"》(台斤)"
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://images.pexels.com/photos/533360/pexels-photo-533360.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940',
                        title='確認交易資訊',
                        text=check_text,
                        actions=[
                            PostbackAction(
                                label='確認送出',
                                text='確認送出',
                                data='where=person_page&action=final_confirm&as=yes&product='+buy_data.product+'&product_id='\
                                        +buy_data.product_id+'&price='+str(buy_data.price)+'&amount='+str(buy_data.amount)
                            ),
                            PostbackAction(
                                label='取消',
                                text='取消',
                                data='where=person_page&action=final_confirm&as=no'
                            )
                        ]
                    )
                )
            )
    except (ValueError,IndexError):
        pass

    try:
        if ( int(get_list_hyphen[0])==2 and type(int(get_list_hyphen[1]))==int and type(int(get_list_hyphen[2]))==int):

            if order_data.price == None:
                order_data.price=int(get_list_hyphen[1])
            if order_data.amount == None:
                order_data.amount=int(get_list_hyphen[2])

            check_text = "訂單的商品是《"+order_data.product+"》\n"\
                            +"單價為《"+str(order_data.price)+"》(元/台斤)\n"+"數量為《"+str(order_data.amount)+"》(台斤)"
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text='Buttons template',
                    template=ButtonsTemplate(
                        thumbnail_image_url='https://images.pexels.com/photos/533360/pexels-photo-533360.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940',
                        title='確認訂單資訊',
                        text=check_text,
                        actions=[
                            PostbackAction(
                                label='確認送出',
                                text='確認送出',
                                data='where=group_page&action=confirm&as=yes&product='+order_data.product+'&price='+str(order_data.price)+'&amount='+str(order_data.amount)
                            ),
                            PostbackAction(
                                label='取消',
                                text='取消',
                                data='where=group_page&action=confirm&as=no'
                            )
                        ]
                    )
                )
            )
    except (ValueError,IndexError):
        pass

    try:
        if ( int(get_list_hyphen[0])==3 and type(int(get_list_hyphen[1]))==int):

            Endpoint='http://%s:5001/order/%s' % (ip_location,int(get_list_hyphen[1]))
            
            Header={'Content-Type':'application/json'}
            
            Response=requests.get(Endpoint,headers=Header)
            
            print(Response)
            print(Response.text)

            order_info = Response.json()

            if (order_info[0]== 'error'):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="無此訂單編號，請重新確認")
                )
            if (order_info[0]== 'invisible'):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="此訂單已被拿走了~\n請選擇其他訂單^_^")
                )
            else:
                #0 product 1 price 2 amount
                product_message = "此訂單的商品為《%s》\n單價為《%s》(元/台斤)\n數量為《%s》(台斤)\n" % (order_info[0],order_info[1],order_info[2])

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=product_message+"是否拿取此訂單",
                                    quick_reply=QuickReply(
                                                items=[
                                                    QuickReplyButton(
                                                        action=PostbackAction(label="是", data=\
                                                            "where=producer_page&action=order_confirm&as=yes&order_id=%s" % (get_list_hyphen[1]))
                                                    ),
                                                    QuickReplyButton(
                                                        action=PostbackAction(label="否", data="where=producer_page&action=confirm&as=no")
                                                    )
                                                ]
                                    )
                    )
                )
    except (ValueError,IndexError):
        pass

if __name__ == "__main__":
    app.run()