from flask import Flask, request, json
import psycopg2
import datetime

######### CONSTANTS & UTILS ########


# 0: psycopg2 unknown error
# 1: invalid param / bad request
# 2: internal error
# 3: auth - access denied
# 4: token not valid
# 5: no active auctions
# 23505: constraint UNIQUE violation
def error(no, text="N/A"):
    return {'error': no, 'text': text}



######### INIT DATABASE CONN ########

conn = psycopg2.connect(user = "aulaspl",
        password = "aulaspl",
        host = "localhost",
        port = "5432",
        database = "projeto")

sql = conn.cursor()
conn.autocommit = True

########## ROUTES ########

api = Flask(__name__)

"""
POST -> signup
    params: username, password, email
    returns: userid
    error: if user/email already exists 
    transaction: not needed, operation is atomic
    
PUT -> login
    params: username, password
    returns: auth token
    error: if access is denied
    transaction: not needed, operation is atomic
"""
@api.route("/dbproj/user", methods=['PUT', 'POST'])
def user():
    
    if request.method == 'POST':
        
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if (username is None or email is None or password is None):
            return error(1)

        try:
            sql.execute("INSERT INTO users (username, email, password) VALUES(%s, %s, MD5(%s)) RETURNING id;", (username, email, password))

        except psycopg2.Error as e:
            conn.rollback()
            return error(e.pgcode)
        
        for row in sql:
            id = row[0]

        return {'userId': id}
       
    elif request.method == 'PUT':

        username = request.form.get('username')
        password = request.form.get('password')

        if (username is None or password is None):
            return error(1)

        try:
            sql.execute("UPDATE users SET token=MD5(random()::text) WHERE username=%s AND password=MD5(%s) RETURNING token;", (username, password))

            token = sql.fetchone()

            if (token is None):
                return error(3)
            
        except psycopg2.Error as e:
            conn.rollback()
            return error(e.pgcode, e.pgerror)

        return {'authToken': token[0]}
        
    else:
        return error(1)
        
"""
POST -> create auction
    params: token, article_id, price, title, description, end_timestamp
"""
@api.route("/dbproj/leilao", methods=['POST'])
def createAuction():

    token = request.form.get('token')
    article_id = request.form.get('artigoId')
    price = request.form.get('precoMinimo')
    title = request.form.get('titulo')
    description = request.form.get('descricao')
    end_date = request.form.get('end_date')

    if (token is None or article_id is None or price is None or title is None or description is None or end_date is None):
        return error(1)

    try:
        # auth 
        sql.execute("SELECT id FROM users WHERE token=%s OR token=%s;", (token, token))

        id = sql.fetchone()

        if (id is None):
            return error(4)

        # insert description entry first
        sql.execute("INSERT INTO descriptions(text) VALUES (%s) RETURNING id;", (description,))

        description_id = sql.fetchone()

        sql.execute("INSERT INTO auctions(article_id, title, price, end_date, last_description_id, seller_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;", (article_id, title, price, end_date, description_id, id))

        auction_id = sql.fetchone()[0]

        sql.execute("UPDATE descriptions SET auctions_id=%s WHERE id=%s;", (auction_id, description_id))

    except psycopg2.Error as e:
        conn.rollback()
        return error(e.pgcode)
    
    return {'leilaoId': auction_id}


@api.route("/dbproj/leiloes", methods=['GET'])
def getAuctions():
    token = request.form.get('token')

    if (token is None):
        return error(1)
    try:
        ts = datetime.datetime.now()
        tsF = ts.strftime("%Y-%m-%d %H:%M:%S")

        sql.execute("SELECT * FROM auctions WHERE timestamp >= %s", (tsF))

        auctions = sql.fetchone()

        if (auctions is None):
            return error(5)

    return {'leilões': auctions}




########## RUN SERVER #########

api.run(port=8080)
conn.close()