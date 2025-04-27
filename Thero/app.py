from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import re
import pymysql
from flask_cors import CORS
import requests

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

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'Your_API_Code_Paste_Here')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

chat_history = []
initial_description_submitted = False
awaiting_question_permission = False
question_flow_active = False
awaiting_motivation_permission = False
awaiting_music_permission = False
awaiting_video_permission = False
awaiting_memes_permission = False
MAX_QUESTIONS = 5
question_count = 0
user_name = "User"
user_condition = "Manageable"

restricted_topics = [
    "sports", "cricket", "football", "food", "restaurants", "cars", "bikes",
    "technology", "money", "business", "stocks", "politics", "cities", "travel",
    "games", "gadgets", "coding", "programming", "shopping", "movies", "series",
    "actor", "actress", "celebrities", "net worth", "luxury", "fashion"
]

casual_allowed_words = [
    "hello", "hi", "okay", "ok", "yes", "no", "thank you", "thanks", "how are you",
    "i am fine", "good", "great", "ready", "sure", "nice", "happy", "awesome"
]

def format_response(response):
    response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)
    response = re.sub(r'\*(.*?)\*', r'\1', response)
    response = re.sub(r'```.*?\n', '', response, flags=re.DOTALL)
    response = re.sub(r'`(.*?)`', r'\1', response)
    response = re.sub(r'\n{2,}', '\n\n', response)
    response = response.replace('*', '')
    response = response.replace("Google", "Thero")
    sentences = re.split(r'(?<=[.!?])\s+', response.strip())[:5]
    short_response = " ".join(sentences)
    return f"{short_response}"

def search_dynamic_content(query):
    search_results = {
        'songs': [
            {"title": "Fight Song", "url": "https://www.youtube.com/watch?v=xo1VInw-SKc"},
            {"title": "Don't Stop Believin'", "url": "https://www.youtube.com/watch?v=1k8craCGpgs"}
        ],
        'videos': [
            {"title": "Believe in Yourself", "url": "https://www.youtube.com/watch?v=mgmVOuLgFB0"},
            {"title": "Unbroken - Motivational Speech", "url": "https://www.youtube.com/watch?v=26U_seo0a1g"}
        ],
        'memes': [
            "Why don’t skeletons fight each other? They don’t have the guts.",
            "Parallel lines have so much in common. It’s a shame they’ll never meet."
        ]
    }
    return search_results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global chat_history, initial_description_submitted, awaiting_question_permission
    global question_flow_active, question_count, awaiting_motivation_permission
    global awaiting_music_permission, awaiting_video_permission, awaiting_memes_permission
    global user_name, user_condition

    user_input = request.json.get('message')
    email = request.json.get('email')

    if not user_input:
        return jsonify({'error': 'No message provided'}), 400

    try:
        if email:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            if result:
                user_name = result[0]
            cursor.close()
            connection.close()

        user_input_lower = user_input.lower()

        if any(topic in user_input_lower for topic in restricted_topics):
            if not any(allowed in user_input_lower for allowed in casual_allowed_words):
                return jsonify({'response': f"Sorry {user_name}, let's stay focused on health, motivation, and emotional well-being topics. Let me know how you're feeling!"})

        chat_history.append({'role': 'user', 'parts': [user_input]})

        if not initial_description_submitted:
            words = len(user_input.strip().split())
            if words < 50:
                return jsonify({'error': 'Please write at least 50 words about your problem.'}), 400
            initial_description_submitted = True
            awaiting_question_permission = True
            response_text = f"Dear {user_name}, thank you for sharing. To understand your situation deeply, I would like to ask you 5 simple questions. Shall we begin?"
            return jsonify({'response': response_text})

        if awaiting_question_permission:
            if any(word in user_input_lower for word in ['yes', 'ok', 'okay', 'ready', 'sure']):
                awaiting_question_permission = False
                question_flow_active = True
                question_count = 1
                prompt = f"Ask question {question_count} to {user_name}. Keep it short with 3-4 multiple-choice options."
                response = model.generate_content(chat_history + [{'role': 'user', 'parts': [prompt]}])
                formatted = format_response(response.text)
                chat_history.append({'role': 'model', 'parts': [formatted]})
                return jsonify({'response': formatted})
            else:
                return jsonify({'response': f"Okay {user_name}, let me know when you are ready to start the questions."})

        if question_flow_active:
            if question_count < MAX_QUESTIONS:
                question_count += 1
                prompt = f"Ask question {question_count} to {user_name}. Keep it short with 3-4 options. Base it on earlier responses."
                response = model.generate_content(chat_history + [{'role': 'user', 'parts': [prompt]}])
                formatted = format_response(response.text)
                chat_history.append({'role': 'model', 'parts': [formatted]})
                return jsonify({'response': formatted})
            else:
                question_flow_active = False
                awaiting_motivation_permission = True
                combined_text = " ".join([msg['parts'][0] for msg in chat_history if msg['role'] == 'user']).lower()
                if any(word in combined_text for word in ['severe', 'overwhelming', 'hopeless', 'suicidal']):
                    user_condition = "Severe"
                elif any(word in combined_text for word in ['struggling', 'difficult', 'painful', 'very sad']):
                    user_condition = "Critical"
                else:
                    user_condition = "Manageable"
                analysis_text = f"Thero: Based on your answers, here is my understanding of your emotional condition: {user_condition}. Would you like me to share a motivational message to uplift you?"
                return jsonify({'response': analysis_text})

        if awaiting_motivation_permission:
            if any(word in user_input_lower for word in ['yes', 'ok', 'okay', 'ready', 'sure']):
                awaiting_motivation_permission = False
                awaiting_music_permission = True
                prompt = f"Write a motivational message of more than 150 words for {user_name} who is facing {user_condition} emotional condition."
                response = model.generate_content([{'role': 'user', 'parts': [prompt]}])
                formatted = format_response(response.text)
                question = "\n\nWould you also like me to suggest motivational songs with YouTube links?"
                return jsonify({'response': formatted + question})
            else:
                return jsonify({'response': f"Okay {user_name}, let me know if you would like to continue."})

        if awaiting_music_permission:
            if any(word in user_input_lower for word in ['yes', 'ok', 'okay', 'ready', 'sure']):
                awaiting_music_permission = False
                awaiting_video_permission = True
                dynamic_content = search_dynamic_content('motivational songs')
                music_response = (
                    "Here are some motivational songs:\n\n"
                    f"1. {dynamic_content['songs'][0]['title']} - {dynamic_content['songs'][0]['url']}\n"
                    f"2. {dynamic_content['songs'][1]['title']} - {dynamic_content['songs'][1]['url']}\n\n"
                    "Would you also like me to suggest motivational YouTube videos?"
                )
                return jsonify({'response': music_response})
            else:
                return jsonify({'response': f"Okay {user_name}, let me know if you want motivational songs later."})

        if awaiting_video_permission:
            if any(word in user_input_lower for word in ['yes', 'ok', 'okay', 'ready', 'sure']):
                awaiting_video_permission = False
                awaiting_memes_permission = True
                dynamic_content = search_dynamic_content('motivational videos')
                video_response = (
                    "Here are some motivational YouTube videos:\n\n"
                    f"1. {dynamic_content['videos'][0]['title']} - {dynamic_content['videos'][0]['url']}\n"
                    f"2. {dynamic_content['videos'][1]['title']} - {dynamic_content['videos'][1]['url']}\n\n"
                    "Would you also like me to share funny memes or jokes to cheer you up?"
                )
                return jsonify({'response': video_response})
            else:
                return jsonify({'response': f"Okay {user_name}, let me know if you want YouTube videos later."})

        if awaiting_memes_permission:
            if any(word in user_input_lower for word in ['yes', 'ok', 'okay', 'ready', 'sure']):
                awaiting_memes_permission = False
                dynamic_content = search_dynamic_content('memes')
                memes_response = (
                    f"Here are some funny memes to cheer you up:\n\n"
                    f"1. {dynamic_content['memes'][0]}\n"
                    f"2. {dynamic_content['memes'][1]}\n\n"
                    "Is there anything else you would like to talk about? I'm here for you!"
                )
                return jsonify({'response': memes_response})
            else:
                return jsonify({'response': f"Okay {user_name}, let me know if you want memes later."})

        response = model.generate_content(chat_history)
        formatted = format_response(response.text)
        chat_history.append({'role': 'model', 'parts': [formatted]})
        return jsonify({'response': formatted})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
