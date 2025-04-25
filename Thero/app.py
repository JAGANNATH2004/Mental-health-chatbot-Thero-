from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import re
import pymysql
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",
        database="login_details"
    )
# Login credentials check
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user:
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'message': 'Login failed'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Creating an account
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'message': 'Email already exists'}), 400

        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'message': 'Account created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API integration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'Your api key here')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

chat_history = []
initial_description_submitted = False

# Formatting response for conciseness with emojis
def format_response(response):
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)
    response = re.sub(r'\*(.*?)\*', r'\1', response)
    response = re.sub(r'```.*?\n', '', response, flags=re.DOTALL)
    response = re.sub(r'`(.*?)`', r'\1', response)
    response = re.sub(r'\n{2,}', '\n\n', response)
    response = response.replace('*', '')
    response = response.replace("Google", "Thero")

    # Shorten response to 5 sentences max
    sentences = re.split(r'(?<=[.!?])\s+', response.strip())[:5]
    short_response = " ".join(sentences)
    return f"{short_response}"

# Start the index.html
@app.route('/')
def index():
    return render_template('index.html')

# Sending the request and receiving the response
@app.route('/chat', methods=['POST'])
def chat():
    global chat_history, initial_description_submitted

    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    try:
        chat_history.append({'role': 'user', 'parts': [user_input]})

        if not initial_description_submitted:
            words = len(user_input.strip().split())
            if words < 50:
                return jsonify({'error': 'Please write at least 50 words about your problem.'}), 400
            else:
                initial_description_submitted = True

        response = model.generate_content(chat_history)
        formatted_response = format_response(response.text)

        chat_history.append({'role': 'model', 'parts': [formatted_response]})

        return jsonify({'response': formatted_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)