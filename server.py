from flask import Flask, request, json, jsonify
import psycopg2

######### CONSTANTS & UTILS ########


# 0: psycopg2 unknown error
# 1: invalid param / bad request
# 2: internal error
# 3: auth - access denied
# 4: token not valid
# 5: auction ended or invalid auctionId
# 6: price lower than current price
# 23505: constraint UNIQUE violation
def error(no, text="N/A"):
    conn.rollback()
    return {'error': no, 'text': text}



######### INIT DATABASE CONN ########

conn = psycopg2.connect(user = "aulaspl",
        password = "aulaspl",
        host = "localhost",
        port = "5432",
        database = "projeto")

sql = conn.cursor()


########## ROUTES ########

api = Flask(__name__)

"""
POST -> signup
    params: none
    body-params: username, password, email
    returns: userid
    error: if user/email already exists 
    
PUT -> login
    params: none
    body-params: username, password
    returns: auth token
    error: if access is denied
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

            conn.commit()
        except psycopg2.Error as e:
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
            conn.commit()
            
            token = sql.fetchone()

            if (token is None):
                return error(3)
            
        except psycopg2.Error as e:
            return error(e.pgcode, e.pgerror)

        return {'authToken': token[0]}
        
    else:
        return error(1)
        
"""
POST -> create auction
    params: token
    body-params: article_id, price, title, description, end_timestamp
    returns: auction ids
    error: if access is denied
"""
@api.route("/dbproj/leilao", methods=['POST'])
def createAuction():

    token = request.args.get('token')
    article_id = request.form.get('artigoId')
    price = request.form.get('precoMinimo')
    title = request.form.get('titulo')
    description = request.form.get('descricao')
    end_date = request.form.get('end_date')

    if (token is None or article_id is None or price is None or title is None or description is None or end_date is None):
        return error(1)

    try:
        # auth 
        sql.execute("SELECT id FROM users WHERE token=%s;", (token,))

        id = sql.fetchone()

        if (id is None):
            return error(4)

        # insert description entry first
        sql.execute("INSERT INTO descriptions(text) VALUES (%s) RETURNING id;", (description,))

        description_id = sql.fetchone()[0]

        sql.execute("INSERT INTO auctions(article_id, title, price, end_date, last_description_id, seller_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;", (article_id, title, price, end_date, description_id, id))

        auction_id = sql.fetchone()[0]

        sql.execute("UPDATE descriptions SET auctions_id=%s WHERE id=%s;", (auction_id, description_id))

        conn.commit()
    
    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)
    
    return {'leilaoId': auction_id}

"""
GET -> get all/ON auction
    params: all (if received returns all auctions)
    returns: auction ids, descriptions
"""
@api.route("/dbproj/leiloes")
def getAuctions():

    allAuctions = request.args.get('all')

    try:
        
        if (allAuctions is None):
            sql.execute("SELECT auctions.id, descriptions.text FROM auctions, descriptions WHERE end_date >= NOW() and descriptions.id = auctions.last_description_id;")
        else:
            sql.execute("SELECT auctions.id, descriptions.text FROM auctions, descriptions WHERE descriptions.id = auctions.last_description_id;")

        auctions = sql.fetchall()
        conn.commit()
        
        r = []

        for row in auctions:
            r.append({'leilaoId': row[0], 'descricao': row[1]})

        

    except psycopg2.Error as e:
        return error(e.pgcode)

    return jsonify(r)


"""
PUT -> edit auction
    params: token
    body-params: title, description
    route: auction_id
    returns: auction id, article id, title, price, end date, highest bidder id, description, seller id
    error: if access is denied
"""
@api.route("/dbproj/leilao/<auction_id>", methods=['PUT'])
def editAuction(auction_id):

    token = request.args.get('token')
    title = request.form.get('title')
    description = request.form.get('description')

    if (title is None and description is None or auction_id is None):
        return error(1)

    try:

        # auth 
        sql.execute("SELECT users.id FROM users, auctions WHERE users.token=%s AND auctions.seller_id = users.id AND auctions.id = %s AND auctions.end_date > NOW();", (token, auction_id))

        id = sql.fetchone()

        if (id is None):
            return error(4)

        if (title is not None):
            sql.execute("UPDATE auctions SET title = %s WHERE id = %s;", (title, auction_id))
        
        if (description is not None):
            sql.execute("INSERT INTO descriptions(text, auctions_id) VALUES (%s, %s) RETURNING id;", (description, auction_id))

            description_id = sql.fetchone()[0]

            sql.execute("UPDATE auctions SET last_description_id = %s WHERE id = %s;", (description_id, auction_id))

        sql.execute("SELECT auctions.id, article_id, title, price, end_date, highest_bidder_id, descriptions.text, seller_id" +
                    " FROM auctions, descriptions" +
                    " WHERE auctions.id = %s AND auctions.last_description_id = descriptions.id;", (auction_id,))

        r = sql.fetchone()

        conn.commit()

    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)
    
    return {'leilaoId': r[0], 'articleId': r[1], 'title': r[2], 'price': r[3], 'end_date': r[4], 'highest_bidder_id': r[5], 'description': r[6], 'seller_id': r[7]} 

"""
GET -> query all/ON auctions
    params:  all (if received returns output off all auctions)
    route: query
    returns: auction id, article id, description
"""
@api.route("/dbproj/leiloes/<query>")
def queryAuctions(query):

    allAuctions   = request.args.get('all')

    if (query is None):
        return error(1)
    
    try:
        # search for a match

        if (query.isnumeric()):
            if (allAuctions is not None):
                sql.execute("SELECT auctions.id, auctions.article_id, descriptions.text FROM auctions, descriptions WHERE (auctions.id = %s) AND (descriptions.id = auctions.last_description_id);", (query, ))

            else:    
                sql.execute("SELECT auctions.id, auctions.article_id, descriptions.text FROM auctions, descriptions WHERE (auctions.id = %s) AND (descriptions.id = auctions.last_description_id) AND (auctions.end_date > NOW());", (query, ))
            
        else:
            if (allAuctions is not None):
                sql.execute("SELECT auctions.id, auctions.article_id, descriptions.text FROM auctions, descriptions " +
                            "WHERE (descriptions.id=auctions.last_description_id) AND (descriptions.text LIKE %s);", ("%" + query + "%",))
            else:
                sql.execute("SELECT auctions.id, auctions.article_id, descriptions.text FROM auctions, descriptions " +
                            "WHERE (descriptions.id=auctions.last_description_id) AND (descriptions.text LIKE %s) AND (auctions.end_date > NOW());", ("%" + query + "%",))

        fetch = sql.fetchall()

        conn.commit()

        r = []
        for row in fetch:
            r.append({'leilaoId': row[0], 'artigoId': row[1], 'descricao': row[2]})


    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)
    
    return jsonify(r)


"""
GET -> get details from an auction
    params: token
    route: auction_id
    returns: auction id, title, article id, price, end date, description, seller id, highest bidder id, messages, biddings
"""
@api.route("/dbproj/leilao/<leilaoId>")
def getDetails(leilaoId):
    
    if (leilaoId is None):
        return error(1)
    
    try:

        sql.execute("SELECT descriptions.text, title, article_id, price, end_date, seller_id, highest_bidder_id FROM auctions, descriptions WHERE auctions.id = %s and auctions.last_description_id = descriptions.id;", (leilaoId, ))       # current description

        r = sql.fetchone()

        sql.execute("SELECT users_id, time_stamp, text FROM messages WHERE auctions_id = %s ORDER BY id;", (leilaoId, ))                   # messages history

        messages = sql.fetchall()
        
        sql.execute("SELECT users_id, time_stamp, price FROM biddings WHERE auctions_id = %s ORDER BY id;", (leilaoId, ))                  # biddings history

        biddings = sql.fetchall()
        
        conn.commit()
        
        mes = []
        for row in messages:
            mes.append({'userId': row[0], 'timestamp': row[1], 'message': row[2]})

        bid = []
        for row in biddings:
            bid.append({'userId': row[0], 'timestamp': row[1], 'bidding': row[2]})

    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)
    
    return {'leilaoId': leilaoId, 'title': r[1], 'article_id': r[2], 'price': r[3], 'end_date': r[4], 'description': r[0], 'seller_id': r[5], 'highest_seller_id': r[6], 'messages': mes, 'biddings': bid}



"""
GET -> get activity from the user
    params: token
    returns: auction id, description
    error: if access is denied
"""
@api.route("/dbproj/meusleiloes")
def getActivity():
    
    token = request.args.get('token')
    
    if (token is None):
        return error(1)

    try:

        # auth 
        sql.execute("SELECT id FROM users WHERE token=%s;", (token,))

        id = sql.fetchone()

        if (id is None):
            return error(4)


        # user as seller and bidder
        sql.execute("SELECT auctions.id, descriptions.text FROM auctions, descriptions WHERE auctions.seller_id = %s and auctions.last_description_id = descriptions.id " + 
                    "UNION " + 
                    "SELECT auctions.id, descriptions.text FROM auctions, descriptions WHERE auctions.last_description_id = descriptions.id and auctions.id IN (SELECT auctions_id FROM biddings WHERE users_id = %s);", (id, id))

        idsB = sql.fetchall()

        conn.commit()

        r = []

        for row in idsB:
            r.append({'leilaoId': row[0], 'description': row[1]})

    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)

    return jsonify(r)


"""
POST -> send message to auction and propagate notifications
    params: token
    route: auction_id
    body-params: text
    returns: {'status': 'success'}
    error: if access is denied, auction id is invalid
"""
@api.route("/dbproj/messages/<auctionID>", methods=['POST'])
def sendMessage(auctionID):

    token = request.args.get('token')
    message = request.form.get('text')
    notifText = "[MESSAGE] New message posted on auction #" + auctionID + "\n\n" + "'" + message + "'"
    
    if (token is None or auctionID is None or message is None):
        return error(1)

    try:

        # auth 
        sql.execute("SELECT id FROM users WHERE token=%s;", (token,))

        id = sql.fetchone()

        if (id is None):
            return error(4)

        # check if auction ID is valid AND online
        sql.execute("SELECT id FROM auctions WHERE id = %s AND end_date > NOW();", (auctionID,))

        auction_id_temp = sql.fetchone()

        if (auction_id_temp is None):
            return error(5)

        sql.execute("INSERT INTO notifications(text, users_id) " +
                    "( SELECT DISTINCT %s, messages.users_id FROM messages WHERE messages.auctions_id=%s AND messages.users_id<>%s" + 
                    " UNION " + 
                    "SELECT %s, auctions.seller_id FROM auctions WHERE auctions.id = %s AND auctions.seller_id<>%s);",
                    (notifText, auctionID, id, notifText, auctionID, id))

        sql.execute("INSERT INTO messages(text, auctions_id, users_id) VALUES (%s, %s, %s);", (message, auctionID, id))

        conn.commit()

    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)

    return {'status': 'success'}

"""
GET -> get list of notifications
    params: token
    returns: text, time stamp
    error: if access is denied
"""
@api.route("/dbproj/notificacoes")
def getNotifications():
    token = request.args.get('token')
    
    if (token is None):
        return error(1)

    try:

        # auth 
        sql.execute("SELECT id FROM users WHERE token=%s;", (token,))

        id = sql.fetchone()

        if (id is None):
            return error(4)

        sql.execute("SELECT text, time_stamp FROM notifications WHERE users_id = %s ORDER BY id;", (id,))

        notifs = sql.fetchall()

        conn.commit()

        r = []
        
        for notif in notifs:
            r.append({'text': notif[0], 'time_stamp': notif[1]})

    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)

    return jsonify(r)

"""
GET -> bid on an auction, notify seller and users in that auction
    params: token
    route: auction_id, value
    returns: {'status': 'success'}
    error: if access is denied, auction id is invalid, value is invalid
"""
@api.route("/dbproj/licitar/<auctionId>/<value>")
def bidAuction(auctionId, value):
    token = request.args.get('token')
    
    if (token is None or auctionId is None or value is None):
        return error(1)

    try:

        # auth 
        sql.execute("SELECT id FROM users WHERE token=%s;", (token,))

        id = sql.fetchone()

        if (id is None):
            return error(4)

        sql.execute("SELECT id FROM auctions WHERE id = %s and NOW() < end_date;", (auctionId,))        # check if auction is still on

        status = sql.fetchone()

        if (status is None):
            return error(5)

        sql.execute("SELECT price FROM auctions WHERE id = %s and price < %s;", (auctionId, value,))

        current_price = sql.fetchone()

        if (current_price is None):
            return error(6)

        # create bid and update auction
        sql.execute("INSERT INTO biddings(price, auctions_id, users_id) VALUES(%s, %s, %s);", (value, auctionId, id))
    
        sql.execute("UPDATE auctions SET highest_bidder_id = %s, price = %s WHERE id = %s;", (id, value, auctionId))
        
        # notification text
        text = "New bidding"        # change text
        
        sql.execute("INSERT INTO notifications(text, users_id) " +
                    "(SELECT DISTINCT %s, biddings.users_id FROM biddings WHERE biddings.auctions_id = %s AND biddings.users_id<>%s" +
                    " UNION " +
                    "SELECT %s, auctions.seller_id FROM auctions WHERE auctions.id = %s);", (text, auctionId, id, text, auctionId))

        conn.commit()

    except psycopg2.Error as e:
        return error(e.pgcode, e.pgerror)

    return {'status': 'success'}

########## RUN SERVER #########

api.run(port=8080)
conn.close()