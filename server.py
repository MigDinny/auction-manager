from flask import Flask, request, json
import psycopg2

######### CONSTANTS & UTILS ########


# 1: invalid param / bad request
# 2: internal error
# 3: auth - access denied
def error(no):
    return {'error': no}



######### INIT DATABASE CONN ########

connection = psycopg2.connect(user = "aulaspl",
        password = "aulaspl",
        host = "localhost",
        port = "5432",
        database = "projeto")

sql = connection.cursor()


########## ROUTES ########

api = Flask(__name__)

@api.route("/dbproj/user", methods=['PUT', 'POST'])
def user():
    
    if request.method == 'POST':
        return {'userId': 3}
       
    elif request.method == 'PUT':
        return {'authToken': 'ab312ef214aabc23412'}
        
    else:
        return error(1)
        


########## RUN SERVER #########

api.run(port=8080)