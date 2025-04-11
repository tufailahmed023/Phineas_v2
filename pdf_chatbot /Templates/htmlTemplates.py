css = '''
<style>
/* Global chat container styles */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Message styles */
.chat-message {
    padding: 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    line-height: 1.6;
}

/* User message styles */
.chat-message.user {
    background-color: #F7F7F8;
}

/* Bot message styles */
.chat-message.bot {
    background-color: #FFFFFF;
    border-bottom: 1px solid #EAEAEA;
}

/* Avatar styling */
.chat-message .avatar {
    width: 30px;
    height: 30px;
    margin-right: 15px;
    flex-shrink: 0;
    border-radius: 2px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* User avatar specific */
.chat-message.user .avatar {
    background-color: #5536DA;
    color: white;
    font-weight: bold;
}

/* Bot avatar specific */
.chat-message.bot .avatar {
    background-color: #19C37D;
    color: white;
    font-weight: bold;
}

/* Message content */
.chat-message .message {
    flex: 1;
    color: #343541;
    font-size: 1rem;
    word-wrap: break-word;
    overflow-wrap: break-word;
}

/* Code block styling */
.chat-message .message pre {
    background-color: #F7F7F8;
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 0.9rem;
}

/* Better markdown formatting */
.chat-message .message p {
    margin-bottom: 0.8rem;
}

.chat-message .message ul, 
.chat-message .message ol {
    margin-left: 1.5rem;
    margin-bottom: 0.8rem;
}

.chat-message .message code {
    background-color: #F7F7F8;
    border-radius: 3px;
    padding: 2px 4px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
}

/* Responsive design */
@media (max-width: 640px) {
    .chat-message {
        padding: 1rem;
    }
    .chat-message .avatar {
        width: 25px;
        height: 25px;
        margin-right: 10px;
    }
}
</style>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <span>AI</span>
    </div>
    <div class="message">{{MSG}}</div>
</div> '''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <span>U</span>
    </div>
    <div class="message">{{MSG}}</div>
    </div> '''