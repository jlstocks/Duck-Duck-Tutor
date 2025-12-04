from flask import Flask, render_template, request, jsonify, session
import os
import json
from datetime import datetime
import secrets

from langchain_community.llms import Ollama

from orchestrations.single_orchestration import SingleOrchestration
from orchestrations.multi_orchestration import MultiOrchestration
from resources.parser import Parser

#configurations
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

CONVERSATIONS_DIR = 'conversations'
os.makedirs(CONVERSATIONS_DIR, exist_ok = True)

#User options
LANGUAGES = ["Python", "Java", "C++", "Go", "C"]
ORCHESTRATIONS = ["single", "multi-agent"]
MODES = {
    "adaptive": "Adaptive (Adjusts to user's needs)",
    "debug": "Debug (Fix code issues)",
    "fundamentals": "Fundamentals (Learn the basics)",
    "examples": "Examples (See sample implementations)",
    "exercises": "Exercises (Practice your skills)",
    "feedback": "Feedback (Review your code)"
}

#Configuration for Ollama
OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_BASE_URL = "http://localhost:11434"

#global parser instance
parser = Parser()

#store orchestrators per session
orchestrators = {}

def get_llm():
    """Initialize and return the Ollama LLM instance"""
    return Ollama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.7
    )

def create_orchestrator(config, session_id):
    """Create the desired orchestration based on user configuration"""
    #Initialize LLM
    llm = get_llm()
    
    #initialize the mode configuration
    mode_config = {
        'language': config.get('language', 'Python'),
        'mode': config.get('mode', 'adaptive')
    }

    log_config = {
        'log_config': {
            'enabled': False  #set to true to debug
        }
    }
    
    #create orchestrator based on user selection
    orchestration_type = config.get('orchestration_type', 'single')
    
    if orchestration_type == 'multi-agent':
        orchestrator = MultiOrchestration(
            llm=llm,
            mode_config=mode_config,
            log_config=log_config,
            revision_enabled=True  #enable tutor revision: tutor considers other agent input during multi-agent orchestration
        )
    else:
        orchestrator = SingleOrchestration(
            llm=llm,
            mode_config=mode_config,
            log_config=log_config
        )
    
    #store the orchestrator for this session
    orchestrators[session_id] = orchestrator
    
    return orchestrator

def get_orchestrator(session_id):
    """Retrieve existing orchestrator for a session"""
    return orchestrators.get(session_id)

def format_conversation_history(messages):
    """
    Format conversation history for the LLM context
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        
    Returns:
        Formatted string with conversation history
    """
    if not messages:
        return ""
    
    #format the conversation history for agent consumption
    history_parts = []
    for msg in messages:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        if role == 'user':
            history_parts.append(f"Student: {content}")
        elif role == 'tutor':
            history_parts.append(f"Tutor: {content}")
    
    return "\n\n".join(history_parts)

@app.route('/')
def index():
    """Main webpage"""
    return render_template('index.html',
                           languages = LANGUAGES,
                           orchestrations = ORCHESTRATIONS,
                           modes = MODES)

@app.route('/chat')
def chat():
    """Chat webpage"""
    if 'config' not in session:
        return render_template('index.html',
                           languages = LANGUAGES,
                           orchestrations = ORCHESTRATIONS,
                           modes = MODES)
    
    config = session['config']
    conversation_id = session.get('conversation_id')

    #load messages if the user is returning
    messages = []
    if conversation_id:
        messages = load_conversation(conversation_id)

    return render_template('chat.html', 
                        config=config,
                        messages=messages,
                        conversation_id=conversation_id)

@app.route('/api/configure', methods = ['POST'])
def configure():
    """Configuration to start a new conversation"""
    data = request.json

    #create config: Defaults = Python, single, adaptive mode
    config = {
        'language': data.get('language', 'Python'),
        'orchestration_type': data.get('orchestration_type', 'single'),
        'mode': data.get('mode', 'adaptive')
    }

    #create a new conversation id for user
    conversation_id = datetime.now().strftime("%Y%m%d_%H%M")

    #store session information
    session['config'] = config
    session['conversation_id'] = conversation_id
    session['messages'] = []

    #create orchestrator for the current session
    try:
        create_orchestrator(config, conversation_id)
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to initialize orchestrator: {str(e)}'
        }), 500

    #save initial conversation
    save_conversation(conversation_id, [], config)

    return jsonify({'success': True, 'conversation_id': conversation_id})

@app.route('/api/send_message', methods = ['POST'])
def send_message():
    """User sends a message and receives a response"""
    data = request.json
    user_message = data.get('message', '')

    #ensure messages field exists in session
    if 'messages' not in session:
        session['messages'] = []
    
    #get conversation ID
    conversation_id = session.get('conversation_id')
    if not conversation_id:
        return jsonify({
            'success': False,
            'error': 'No active conversation. Please start a new session.'
        }), 400

    #add a new user message
    session['messages'].append({
        'role': 'user',
        'content': user_message
    })
    
    #save after adding user message to prevent loss of progress
    save_conversation(conversation_id, session['messages'], session['config'])

    #get orchestration type for this session
    orchestrator = get_orchestrator(conversation_id)
    
    if not orchestrator:
        #attempt to create orchestrator if it is not found
        config = session.get('config', {})
        try:
            orchestrator = create_orchestrator(config, conversation_id)
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to get orchestrator: {str(e)}'
            }), 500

    #get conversation history (excluding the current message) for the agent
    history = session['messages'][:-1]
    conversation_context = format_conversation_history(history)

    try:
        #build state with user message and conversation history
        state = {
            'user_input': user_message,
            'conversation_history': conversation_context
        }
        
        #execute the selected orchestration
        result_state = orchestrator.run_workflow(user_message, context=conversation_context)
        
        #Parse final answer
        llm_response = parser.extract_final_response(result_state)
        
    except Exception as e:
        #handle errors during agent interaction
        llm_response = f"I apologize, but I encountered an error processing your request: {str(e)}"
        print(f"Error in workflow: {str(e)}")

    #add LLM response to messages
    session['messages'].append({
        'role': 'tutor',
        'content': llm_response
    })

    #save conversation session
    save_conversation(session['conversation_id'], session['messages'], session['config'])

    return jsonify({
        'success': True,
        'response': llm_response
    })

@app.route('/api/conversations')
def list_conversations():
    """Get list of all conversations for user"""
    conversations = []

    #retrieve any conversations from conversations dir
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            #open previous conversation
            try:
                with open(filepath, 'r') as f:
                    #load previous conversation and append to conversation data
                    data = json.load(f)
                    conversations.append({
                        'id': data['id'],
                        'config': data['config'],
                        'message_count': len(data['messages']),
                        'update_time': data.get('update_time', '')
                    })
            except Exception as e:
                print(f"Error loading conversation {filename}: {e}")
                continue
    #sort conversations by most recent update time
    conversations.sort(key = lambda x: x['update_time'], reverse = True)

    return jsonify(conversations)

@app.route('/api/load_conversation/<conversation_id>')
def load_conversation_route(conversation_id):
    """Load a selected conversation for a user"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")

    #ensure that the file exists
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            session['conversation_id'] = conversation_id
            session['config'] = data['config']
            session['messages'] = data['messages']
            
            #recreate the selected orchestration for the user
            try:
                create_orchestrator(data['config'], conversation_id)
            except Exception as e:
                print(f"Warning: Could not recreate orchestrator: {str(e)}")

            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'error': f'Error loading conversation: {str(e)}'}), 500
    
    #return an error if filepath not found
    return jsonify({'success': False, 'error': 'Conversation not found'}), 404

def save_conversation(conversation_id, messages, config):
    """Helper method to save conversation to a file"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")

    data = {
        'id': conversation_id,
        'messages': messages,
        'config': config,
        'update_time': datetime.now().isoformat()
    }

    #dump conversation data into defined file
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {e}")

def load_conversation(conversation_id):
    """Load conversation from file"""
    filepath = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('messages', [])
        except Exception as e:
            print(f"Error loading conversation messages: {e}")
            return []
    
    return []

if __name__ == '__main__':
    app.run(debug = True, port = 5000)