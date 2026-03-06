from flask import Flask, render_template, request, jsonify, session
import os
import re
import pymysql
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'super-secret-default-key')
CORS(app)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables. Please check your .env file.")

# Initialize the LangChain LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.7
)

# Define the Prompt Template
template = """You are an empathetic, intelligent mental health assistant named Thero. 
Your ONLY purpose is to provide support, guidance, and active listening for emotional, psychological, and mental well-being topics.
If the user's input is NOT related to mental health, emotions, therapy, stress, or well-being, you must politely decline to answer, remind them that you are a dedicated mental health assistant, and ask how they are feeling emotionally today.

If it is a mental health topic: Provide a comprehensive, actionable, and deeply empathetic recommendation tailored specifically to their situation. 
And also If user is requesting any audio songs or video songs suggest them with direct links with it's title.
Your entire response MUST be strictly under 100 words.

Current conversation history:
{history}
User: {input}
Thero:"""

PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)

# Database connection
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', "localhost"),
        user=os.getenv('DB_USER', "root"),
        password=os.getenv('DB_PASSWORD', "Your_password"), 
        database=os.getenv('DB_NAME', "Your DB_name")
    )

# Login credentials check
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(silent=True)
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400

        email = data.get('email')
        password = data.get('password')

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
                user = cursor.fetchone()
        finally:
            connection.close()

        if user:
            session['user_email'] = email
            session['user_name'] = data.get('name', 'User')
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'message': 'Login failed'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Creating an account
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json(silent=True)
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Missing email or password'}), 400

        email = data.get('email')
        password = data.get('password')

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    return jsonify({'message': 'Email already exists'}), 400

                cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
                connection.commit()
        finally:
            connection.close()

        return jsonify({'message': 'Account created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(silent=True)
        user_input = data.get('message') if data else None
        
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        # Load existing history if it exists
        chat_history = []
        if 'chat_history' in session:
            for interaction in session['chat_history']:
                if interaction['type'] == 'human':
                    chat_history.append(HumanMessage(content=interaction['text']))
                elif interaction['type'] == 'ai':
                    chat_history.append(AIMessage(content=interaction['text']))
        else:
            session['chat_history'] = []

        try:
            # Format the conversation history string
            history_str = ""
            for msg in chat_history:
                if isinstance(msg, HumanMessage):
                    history_str += f"User: {msg.content}\n"
                elif isinstance(msg, AIMessage):
                    history_str += f"Thero: {msg.content}\n"

            # Generate the response utilizing the built prompt
            final_prompt = PROMPT.format(history=history_str, input=user_input)
            response = llm.invoke(final_prompt)
            raw_response = response.content
            
            # Save the new interaction back to the Flask session so it persists for the next request
            session['chat_history'].append({'type': 'human', 'text': user_input})
            session['chat_history'].append({'type': 'ai', 'text': raw_response})
            
            # Simple summarization if history gets too long (over 10 messages)
            if len(session['chat_history']) > 10:
                # Keep last 6 messages (3 turns)
                session['chat_history'] = session['chat_history'][-6:]
                
            session.modified = True
            
            # Clean up formatting for the frontend (removing markdown)
            response_text = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_response) 
            response_text = re.sub(r'\*(.*?)\*', r'\1', response_text)     
            response_text = re.sub(r'```.*?\n', '', response_text, flags=re.DOTALL) 
            response_text = re.sub(r'`(.*?)`', r'\1', response_text)       
            response_text = response_text.replace('*', '')                 
            response_text = re.sub(r'\n{2,}', '\n', response_text)         


        except ValueError:
            response_text = "I'm sorry, I cannot respond to that prompt due to safety guidelines."
        except Exception as api_err:
            app.logger.error(f"Generate content error: {api_err}")
            response_text = "Oops! Thero had a little trouble thinking. Give me a moment and try asking me again."

        return jsonify({'response': response_text})

    except Exception as e:
        app.logger.error(f"Chat route error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
