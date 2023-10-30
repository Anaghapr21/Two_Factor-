from flask import Flask, request, jsonify
import mysql.connector
import requests
import secrets
import uuid
import json
import random
app = Flask(__name__)

# Configuration for MySQL
mysql_host = 'localhost'
mysql_user = 'anagha'
mysql_password = 'anagha123'
mysql_database = 'otp'

# MySQL Connection
mysql = mysql.connector.connect(
    host='localhost',
    user='anagha',
    password='anagha123',
    database='otp'
)
@app.route('/api/v1/twofactor/create_delivery_method', methods=['POST'])
def create_delivery_method():
    try:
        data = request.get_json()
        name = data.get('name')
        target = data.get('target')

        if name and target:
            insert_delivery_method(name, target)
            return jsonify({"message": "Delivery method created"})
        else:
            return jsonify({"error": "Name and target are required fields."}, 400)
    except Exception as e:
        return jsonify({"error": str(e)})
    
def insert_delivery_method(name, target):
    cur = mysql.cursor()
    cur.execute("INSERT INTO delivery_methods (name, target) VALUES (%s, %s)", (name, target))
    mysql.commit()
    cur.close() 


# Create a function to fetch delivery methods from MySQL
def fetch_delivery_methods():
    cur = mysql.cursor()
    cur.execute("SELECT name, target FROM delivery_methods")
    result = cur.fetchall()
    cur.close()
    return result

@app.route('/api/v1/twofactor/get_delivery_methods', methods=['GET'])
def get_delivery_methods():
    try:

        delivery_methods = fetch_delivery_methods()
        return jsonify(delivery_methods)
    except Exception as e:
        return jsonify({"error": str(e)})


# Function to generate a random 6-digit OTP
def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

# # Function to store OTP in the database
# def store_otp_in_database(otp, delivery_method):
#     cur = mysql.cursor()
#     cur.execute("INSERT INTO otps (otp, delivery_method) VALUES (%s, %s)",
#                 (otp, delivery_method))
#     mysql.commit()
#     cur.close()

# @app.route('/api/v1/twofactor/request_otp', methods=['POST'])
# def request_otp():
#     try:
#         data=request.json
#         delivery_method = request.args.get('deliveryMethod')
#         extended_token = request.args.get('extendedToken')
#         # user_id = 2  # Replace with the actual user's ID

#     # Generate a random OTP
#         otp = generate_otp()

#     # Store the OTP in the database
#         store_otp_in_database(otp, delivery_method)

#         return jsonify({"otp": otp})
#     except Exception as e:
#         return jsonify({"error":"An error occurred","details":str(e)})

# Create a function to validate OTP and create an access token


@app.route('/api/v1/twofactor/request_otp', methods=['POST'])
def request_otp():
    try:
        data = request.json
        delivery_method = data['deliveryMethod']['name']
        extended_token = data.get('extendedToken', False)
        request_time = data['requestTime']/1000
        token_live_time = data['tokenLiveTimeInSec']
        target = data['deliveryMethod']['target']
         # Generate a random OTP
        otp = generate_otp()

        # Store the OTP request data in MySQL (you can customize this part)
        cur = mysql.cursor()
        cur.execute("INSERT INTO otps (delivery_method, extended_token, request_time, token_live_time, target,otp) VALUES (%s, %s, %s, %s, %s,%s)",
                    (delivery_method, extended_token, request_time, token_live_time, target,otp))
        mysql.commit()
        cur.close()

        # Implement logic to generate and send OTP to the target (e.g., via SMS)

        return jsonify({"otp":otp})
    except Exception as e:
        return jsonify({"error": str(e)})
def validate_otp_and_generate_token(token,user_id):
    cur = mysql.cursor()
    cur.execute("SELECT otp FROM otps WHERE id = %s", (user_id,))
    stored_otp = cur.fetchone()
    cur.close()

    if stored_otp and token == stored_otp[0]:
        # OTP is valid, generate an access token (secure token)
        access_token = secrets.token_hex(32)  # Generates a 64-character hexadecimal token
        return access_token
    else:
        return None

# Create a function to invalidate the access token (simply remove it from the database in this example)
def invalidate_access_token(access_token):
    cur = mysql.cursor()
    cur.execute("DELETE FROM access_tokens WHERE token = %s", (access_token,))
    mysql.commit()
    cur.close()

# @app.route('/api/v1/twofactor/validate_otp', methods=['POST'])
# def validate_otp_endpoint():
#     token = request.json.get('token')
#     # user_id = 3 # Replace with the actual user's ID
#     id=data.get('id')
#     try:
#         data=request.json
#         access_token = validate_otp_and_generate_token(token)
#         if access_token:
#         # Store the access token in the database for future reference
#             cur = mysql.cursor()
#             cur.execute("INSERT INTO access_tokens (id,token) VALUES (%s)", (access_token,id))
#             mysql.commit()
#             cur.close()
#             return jsonify({"access_token": access_token})
#         else:
#             return jsonify({"error": "Invalid OTP"})
#     except Exception as e:
#         return jsonify({"error":"An error occurred","details":str(e)})


@app.route('/api/v1/twofactor/validate_otp', methods=['POST'])
def validate_otp_endpoint():
    try:
        data = request.json
        token = data.get('token')
        user_id = data.get('id')  # Assuming the ID is provided in the JSON data

        if token is not None and user_id is not None:
            access_token = validate_otp_and_generate_token(token, user_id)
            if access_token:
                # Store the access token in the database for future reference
                cur = mysql.cursor()
                cur.execute("INSERT INTO access_tokens (token, user_id) VALUES (%s, %s)", (access_token, user_id))
                mysql.commit()
                cur.close()
                return jsonify({"access_token": access_token})
            else:
                return jsonify({"error": "Invalid OTP"})
        else:
            return jsonify({"error": "Token and user ID are required in the request data"})
    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)})


@app.route('/api/v1/twofactor/invalidate_access_token', methods=['POST'])
def invalidate_access_token_endpoint():
    access_token = request.json.get('token')

    # Invalidate the access token by removing it from the database
    invalidate_access_token(access_token)
    
    return jsonify({"message": "Access token invalidated"})


if __name__ == '__main__':
    app.run(debug=True)
