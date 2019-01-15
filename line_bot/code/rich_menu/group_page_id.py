#!/usr/bin/python
#coding:utf-8

import json
import requests


secretFileContentJson=json.load(open("../line_key",'r'))


#group_page
menuJson=json.load(open("./menu_json/group_page",'r'))

createMenuEndpoint = 'https://api.line.me/v2/bot/richmenu'
createMenuRequestHeader={'Content-Type':'application/json','Authorization':'Bearer %s' % secretFileContentJson["channel_access_token"]}

#print(createMenuRequestHeader)

lineCreateMenuResponse = requests.post(createMenuEndpoint,headers=createMenuRequestHeader,data=json.dumps(menuJson))

print(lineCreateMenuResponse)
print(lineCreateMenuResponse.text)
print("-----")
# 取得菜單Id 
uploadRichMenuId=json.loads(lineCreateMenuResponse.text).get("richMenuId")
print(uploadRichMenuId)
#'https://api.line.me/v2/bot/richmenu/{richMenuId}/content'
print("-----")
# 設定Line的遠端位置
uploadMenuEndpoint='https://api.line.me/v2/bot/richmenu/%s/content' % uploadRichMenuId
#print(uploadMenuEndpoint)

# 設定消息的基本安全憑證
uploadMenuRequestHeader={'Content-Type':'image/jpeg','Authorization':'Bearer %s' % secretFileContentJson["channel_access_token"]}

# 上傳照片
uploadImageFile=open("./menu_picture/group_page.jpg",'rb')
lineUploadMenuResponse=requests.post(uploadMenuEndpoint,headers=uploadMenuRequestHeader,data=uploadImageFile)

#print(lineUploadMenuResponse)
print(lineUploadMenuResponse.text)

#輸出文件
output = open("../group_page_id","w")
output.write(str(lineCreateMenuResponse.text))
output.close()