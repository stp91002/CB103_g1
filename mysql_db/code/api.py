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
conn = pymysql.connect(host='chatbot_db', port=3306, user='root', passwd='iii', db='chatbot_db', charset='utf8mb4')

# 方便用來跟mysql互動
cur = conn.cursor()

transaction_list=["番茄","香蕉","橘子","高麗菜","玉米"]

# 存入使用者
@app.route('/users', methods=['POST'])
def add_user():
    # 定義儲存時間
    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users = request.get_json()

    error = None

    # 抓出name的值
    cur.execute('SELECT display_name FROM chatbot_db.Users WHERE user_id = ("%s")' % (users['user_id']))
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
                "INSERT INTO chatbot_db.Users (user_id, display_name,picture_url,user_type, join_datetime,last_load) VALUES ( %s,%s,%s,%s,%s,%s)")
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

#獲得user_type
@app.route('/users/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def read_user_type(user_id):
    cur.execute(
        'SELECT user_type FROM chatbot_db.Users WHERE user_id = ("%s")' % (user_id)
        )
    #將剛剛execute的資料取出來
    user_type = cur.fetchone()
    print(user_type)
    return jsonify(user_type)


#修改user_type
@app.route('/users/alter/<user_id>',methods=['POST'])
#特別注意這邊有打userid，url parameter就是這樣使用
def join_user_type(user_id):

    last_load = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    users = request.get_json()

    updatesql = (
                "UPDATE chatbot_db.Users SET user_type = %s , last_load = %s WHERE user_id = (%s)"
                )
    value = (users['user_type'],last_load,user_id)

    cur.execute(updatesql, value)

    conn.commit()
    result = {"status_describe": "success alter"}

    return jsonify(result)

#新增商品
@app.route('/product/<user_id>',methods=['POST'])
#特別注意這邊有打userid，url parameter就是這樣使用
def insert_product(user_id):

    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    last_load = join_datetime
    product_type = "visible"
    product_info = request.get_json()

    insertsql = (
                "INSERT INTO chatbot_db.Products (user_id, product,price,amount,product_type, join_datetime,last_load) VALUES ( %s,%s,%s,%s,%s,%s,%s)"
                )
    value = (user_id,product_info['product'],product_info['price'],product_info['amount'],product_type,join_datetime,last_load)

    cur.execute(insertsql, value)

    conn.commit()
    result = {"status_describe": "success insert product"}

    return jsonify(result)


#以商品編號查詢商品狀態
@app.route('/product/<product_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def read_product_info(product_id):

    cur.execute(
        'SELECT product_type FROM chatbot_db.Products WHERE product_id = ("%s")' % (product_id)
        )
    product_type = cur.fetchone()

    error = None

    if product_type == None:
        product_info = ("error",)

    elif not product_type[0] == 'visible':

        error = 'product_id {} is not visible.'.format(product_id)
        print(error)

        product_info = ("invisible",)

    else:
        cur.execute(
            'SELECT product,price,amount FROM chatbot_db.Products WHERE product_id = ("%s")' % (product_id)
            )
        product_info = cur.fetchone()

    return jsonify(product_info)


#交易：修改Products及新增交易紀錄
@app.route('/product/buy/<user_id>',methods=['POST'])
#特別注意這邊有打userid，url parameter就是這樣使用
def product_transaction(user_id):

    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    last_load = join_datetime

    product_info = request.get_json()

    buyer_id = user_id

    product_type = 'visible'

    cur.execute(
        'SELECT amount,user_id FROM chatbot_db.Products WHERE product_id = ("%s")' % (product_info['product_id'])
        )
    product_query = cur.fetchone()

    print(product_query)

    seller_id = product_query[1]


    if (int(product_info['amount']) > product_query[0]):

        error = 'not enough'

        result = {"status_describe": "{}".format(error)}

        transaction_result = ("not_enough",)

    else:
        new_amount = int(product_query[0])-int(product_info['amount'])
        #新增交易紀錄
        insertsql = (
                "INSERT INTO chatbot_db.Transactions (buyer_id,seller_id,product_id, product,price,amount, join_datetime) VALUES ( %s,%s,%s,%s,%s,%s,%s)"
                )
        value = (buyer_id,seller_id,product_info['product_id'],product_info['product'],product_info['price'],product_info['amount'],join_datetime)
    
        cur.execute(insertsql, value)

        conn.commit()

        if(new_amount == 0):
            product_type = 'invisible'

        #更新商品資料
        updatesql = (
                    "UPDATE chatbot_db.Products SET amount = %s ,product_type = %s , last_load = %s WHERE product_id = (%s)"
                    )
        value = (new_amount,product_type,last_load,product_info['product_id'])

        cur.execute(updatesql, value)

        conn.commit()

        transaction_result = ("success",)

        result = {"status_describe": "successful deal"}

    print(result)

    return jsonify(transaction_result)


#新增訂單
@app.route('/order/<user_id>',methods=['POST'])
#特別注意這邊有打userid，url parameter就是這樣使用
def insert_order(user_id):

    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    last_load = join_datetime
    order_type = "visible"
    order_info = request.get_json()

    insertsql = (
                "INSERT INTO chatbot_db.Orders (user_id, product,price,amount,order_type, join_datetime,last_load) VALUES ( %s,%s,%s,%s,%s,%s,%s)"
                )
    value = (user_id,order_info['product'],order_info['price'],order_info['amount'],order_type,join_datetime,last_load)

    cur.execute(insertsql, value)

    conn.commit()
    result = {"status_describe": "success insert order"}

    return jsonify(result)

#以訂單編號查詢訂單狀態
@app.route('/order/<order_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def read_order_info(order_id):

    cur.execute(
        'SELECT order_type FROM chatbot_db.Orders WHERE order_id = ("%s")' % (order_id)
        )
    order_type = cur.fetchone()

    error = None

    if order_type == None:
        order_info = ("error",)

    elif not order_type[0] == 'visible':

        error = 'order_id {} is not visible.'.format(order_id)
        print(error)

        order_info = ("invisible",)

    else:
        cur.execute(
            'SELECT product,price,amount FROM chatbot_db.Orders WHERE order_id = ("%s")' % (order_id)
            )
        order_info = cur.fetchone()

    return jsonify(order_info)

#拿訂單：修改Orders及新增訂單交易紀錄
@app.route('/order/get/<user_id>',methods=['POST'])
#特別注意這邊有打userid，url parameter就是這樣使用
def order_transaction(user_id):

    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    last_load = join_datetime

    order_info = request.get_json()

    seller_id = user_id

    cur.execute(
        'SELECT user_id FROM chatbot_db.Orders WHERE order_id = ("%s")' % (order_info['order_id'])
        )
    order_query = cur.fetchone()

    buyer_id = order_query[0]

    #新增交易紀錄
    insertsql = (
            "INSERT INTO chatbot_db.Order_transactions (buyer_id,seller_id,order_id,join_datetime) VALUES (%s,%s,%s,%s)"
            )
    value = (buyer_id,seller_id,order_info['order_id'],join_datetime)
    
    cur.execute(insertsql, value)

    conn.commit()
    
    order_type = 'invisible'

    #更新商品資料
    updatesql = (
                "UPDATE chatbot_db.Orders SET order_type = %s , last_load = %s WHERE order_id = (%s)"
                )
    value = (order_type,last_load,order_info['order_id'])

    cur.execute(updatesql, value)

    conn.commit()

    result = {"status_describe": "successful deal"}

    return jsonify(result)


#個人及團體得到商品清單
@app.route('/get_product_lists/<product>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def get_product_lists(product):

    cur.execute(
        'SELECT product_id,price,amount,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Products WHERE product = ("%s") AND product_type = "visible"' % (transaction_list[int(product)])
        )
    product_lists = cur.fetchall()


    return jsonify(product_lists)

#個人及團體的交易清單
@app.route('/get_person_transaction_lists/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def get_person_transaction_lists(user_id):

    cur.execute(
        'SELECT transaction_id,product_id,product,price,amount,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Transactions WHERE buyer_id = ("%s") ' % (user_id)
        )
    person_transaction_lists = cur.fetchall()


    return jsonify(person_transaction_lists)

#公司團體的訂單
@app.route('/get_order_lists/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def get_order_lists(user_id):

    cur.execute(
        'SELECT order_id,product,price,amount,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Orders WHERE user_id = ("%s") ' % (user_id)
        )
    order_lists = cur.fetchall()


    return jsonify(order_lists)


#公司團體的訂單交易清單
@app.route('/get_order_transaction_lists/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def get_order_transaction_lists(user_id):

    cur.execute(
        'SELECT order_transaction_id,order_id,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Order_transactions WHERE buyer_id = ("%s") ' % (user_id)
        )
    order_transaction_lists = cur.fetchall()


    return jsonify(order_transaction_lists)

#生產者查看商品清單
@app.route('/read_product_lists/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def read_product_lists(user_id):

    cur.execute(
        'SELECT product_id,product,price,amount,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Products WHERE user_id = ("%s") ' % (user_id)
        )
    product_lists = cur.fetchall()


    return jsonify(product_lists)

#生產者查看訂單清單
@app.route('/producer_get_order_lists/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def producer_get_order_lists(user_id):

    cur.execute(
        'SELECT order_id,product,price,amount,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Orders WHERE order_type = "visible" '
        )
    order_lists = cur.fetchall()


    return jsonify(order_lists)

#生產者的交易清單
@app.route('/get_producer_transaction_lists/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def get_producer_transaction_lists(user_id):

    cur.execute(
        'SELECT transaction_id,product_id,product,price,amount,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Transactions WHERE seller_id = ("%s") ' % (user_id)
        )
    person_transaction_lists = cur.fetchall()


    return jsonify(person_transaction_lists)

#生產者的訂單交易清單
@app.route('/get_producer_order_transaction_lists/<user_id>',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def get_producer_order_transaction_lists(user_id):

    cur.execute(
        'SELECT order_transaction_id,order_id,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime) FROM chatbot_db.Order_transactions WHERE seller_id = ("%s") ' % (user_id)
        )
    order_transaction_lists = cur.fetchall()


    return jsonify(order_transaction_lists)

#品質反饋
@app.route('/feedback',methods=['POST'])
#特別注意這邊有打userid，url parameter就是這樣使用
def feedback():

    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    feedback_info = request.get_json()

    insertsql = (
                "INSERT INTO chatbot_db.Feedbacks (content, join_datetime) VALUES ( %s,%s)"
                )
    value = (feedback_info['content'],join_datetime)

    cur.execute(insertsql, value)

    conn.commit()
    result = {"status_describe": "success insert feedback"}

    return jsonify(result)

#品質反饋清單
@app.route('/feedback_list',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def feedback_list():

    cur.execute(
        'SELECT feedback_id,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime),content FROM chatbot_db.Feedbacks' 
        )
    feedback_lists = cur.fetchall()


    return jsonify(feedback_lists)

#問題回報
@app.route('/question',methods=['POST'])
#特別注意這邊有打userid，url parameter就是這樣使用
def question():

    join_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    question_info = request.get_json()

    insertsql = (
                "INSERT INTO chatbot_db.Questions (content, join_datetime) VALUES ( %s,%s)"
                )
    value = (question_info['content'],join_datetime)

    cur.execute(insertsql, value)

    conn.commit()
    result = {"status_describe": "success insert question"}

    return jsonify(result)

#問題回報清單
@app.route('/question_list',methods=['GET'])
#特別注意這邊有打userid，url parameter就是這樣使用
def question_list():

    cur.execute(
        'SELECT question_id,YEAR(join_datetime),MONTH(join_datetime),DAY(join_datetime),content FROM chatbot_db.Questions' 
        )
    question_lists = cur.fetchall()


    return jsonify(question_lists)

if __name__ == '__main__':
    # 運行flask server，運行在0.0.0.0:5000
    # 要特別注意假如運行在127.0.0.1的話，會變成只有本機連的到，外網無法
    app.run(host='0.0.0.0', port=5000)
