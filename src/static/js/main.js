//the current state
let currentConversationId = null;

//load all conversations during page loading
document.addEventListener('DOMContentLoaded', function() {
    loadConversations();
    
    //add support for the enter key during chat
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});

//display the configuration screen for the user to make selections
function showConfig() {
    document.getElementById('config-screen').style.display = 'block';
    document.getElementById('chat-screen').style.display = 'none';
}

//show the chat screen where the user may interact with agents
function showChat() {
    document.getElementById('config-screen').style.display = 'none';
    document.getElementById('chat-screen').style.display = 'flex';
}

//function to create a new session with new configurations
async function startSession() {
    const language = document.getElementById('language').value;
    const orchestration = document.getElementById('orchestration').value;
    const mode = document.getElementById('mode').value;
    
    const response = await fetch('/api/configure', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            language: language,
            orchestration_type: orchestration,
            mode: mode
        })
    });
    
    const data = await response.json();
    
    if (data.success) {
        currentConversationId = data.conversation_id;
        
        //update chat title based on selected language
        document.getElementById('chat-title').textContent = `${language} Tutor`;
        
        //clear messages from conversation
        document.getElementById('chat-messages').innerHTML = '';

        showChat();
        
        //reload the conversations list
        loadConversations();
    }
}

//function to send a message to agents
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    //clear input
    input.value = '';
    
    //add the user message to the UI after sending
    addMessage('user', message);
    
    //display loading while the agent is processing
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.id = 'loading';
    loadingDiv.textContent = 'Loading...';
    document.getElementById('chat-messages').appendChild(loadingDiv);
    scrollToBottom();
    
    //send the user message to the backend for processing
    const response = await fetch('/api/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message
        })
    });
    
    const data = await response.json();
    
    //remove loading popup
    document.getElementById('loading').remove();
    
    if (data.success) {
        addMessage('assistant', data.response);
    }
}

//add agent response to the UI
function addMessage(role, content) {
    const messagesDiv = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const roleDiv = document.createElement('div');
    roleDiv.className = 'message-role';
    roleDiv.textContent = role === 'user' ? 'You' : 'Tutor';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(roleDiv);
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    
    scrollToBottom();
}

function scrollToBottom() {
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function loadConversations() {
    const response = await fetch('/api/conversations');
    const conversations = await response.json();
    
    const listDiv = document.getElementById('conversations-list');
    listDiv.innerHTML = '';
    
    if (conversations.length === 0) {
        listDiv.innerHTML = '<p style="color: #7f8c8d; font-size: 12px;">No previous conversations</p>';
        return;
    }
    
    conversations.forEach(conv => {
        const button = document.createElement('button');
        button.className = 'btn btn-conversation';
        if (conv.id === currentConversationId) {
            button.classList.add('active');
        }
        
        const config = conv.config;
        button.textContent = `${config.language} - ${config.orchestration_type}`;
        button.onclick = () => loadConversation(conv.id);
        
        listDiv.appendChild(button);
    });
}

//Load a specific conversation that the user selects
async function loadConversation(conversationId) {
    const response = await fetch(`/api/load_conversation/${conversationId}`);
    const result = await response.json();
    
    if (result.success) {
        currentConversationId = conversationId;
        const data = result.data;
        
        //update the title of a selected chat
        document.getElementById('chat-title').textContent = `${data.config.language} Tutor`;
        
        //reload messages
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML = '';
        
        data.messages.forEach(msg => {
            addMessage(msg.role, msg.content);
        });
        
        showChat();
        loadConversations();
    }
}