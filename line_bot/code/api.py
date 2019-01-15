# 製作flask環境
from flask import Flask, request, jsonify
import datetime
import pymysql

# # 增加等待時間，為了整合的需要所新增的
# import time

# time.sleep(100)

# 呼叫出Flask
app = Flask(__name__)

# 建立與mysql的連線
conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='iii', db='linebot_db', charset='utf8mb4')

# 方便用來跟mysql互動
cur = conn.cursor()


# 存入使用者
@app.route('/users', methods=['POST'])
def add_user():
    # 定義儲存時間
    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users = request.get_json()

    error = None

    # 抓出name的值
    cur.execute('SELECT display_name FROM linebot_db.Users WHERE user_id = ("%s")' % (users['user_id']))
    display_name = cur.fetchone()

    # 檢查是否第一次follow
    if not display_name == None:
        # 不是第一次follow，製作錯誤訊息
        error = 'User {} {} is not a new follower.'.format(users['user_id'], display_name)

        # 製作一個錯誤的描述(json)
        result = {"status_describe": "{}".format(error)}

    else:
        # 建查 user_id 是否存在
        if users['user_id'] == None:
            error = 'The user_id of user is None !'
            result = {"status_describe": "{}".format(error)}

        # 檢查 display_name 是否存在
        elif users['display_name'] == None:
            error = 'The name of user is None !'
            result = {"status_describe": "{}".format(error)}

        else:
            last_load = join_datetime

            user_type = "visitor"

            insertsql = (
                "INSERT INTO linebot_db.Users (user_id, display_name,picture_url,user_type, join_datetime,last_load) VALUES ( %s,%s,%s,%s,%s,%s)")
            value = (users['user_id'],
                     users['display_name'],
                     users['picture_url'],
                     user_type,
                     join_datetime,
                     last_load)

            cur.execute(insertsql, value)

            # 將資料送進資料庫中
            conn.commit()
            # 傳回正確訊息
            result = {"status_describe": "success add user"}


    return jsonify(result)

if __name__ == '__main__':
    # 運行flask server，運行在0.0.0.0:5000
    # 要特別注意假如運行在127.0.0.1的話，會變成只有本機連的到，外網無法
    app.run(host='0.0.0.0', port=5000)
