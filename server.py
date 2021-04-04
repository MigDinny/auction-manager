from flask import Flask, request, json
import psycopg2

######### CONSTANTS & UTILS ########


# 0: psycopg2 unknown error
# 1: invalid param / bad request
# 2: internal error
# 3: auth - access denied
# 23505: constraint UNIQUE violation
def error(no):
    return {'error': no}



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
    transaction: needed becase we need rollback
    
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
            sql.execute("INSERT INTO users (username, email, password) VALUES(%s, %s, %s) RETURNING id;", (username, email, password))

        except psycopg2.Error as e:
            conn.rollback()
            return error(e.pgcode)
        
        for row in sql:
            id = row[0]

        return {'userId': id}
       
    elif request.method == 'PUT':
        return {'authToken': 'ab312ef214aabc23412'}
        
    else:
        return error(1)
        


########## RUN SERVER #########

api.run(port=8080)
conn.close()