css = '''
<style>
.chat-message {
    padding: 1.5rem;
    border-radius: 1.5rem;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    backdrop-filter: blur(8px);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
    transition: all 0.3s ease-in-out;
}

.chat-message.user {
    background: linear-gradient(135deg, #2e3b4e, #3a465e);
    border-left: 6px solid #00ff99;
}

.chat-message.bot {
    background: linear-gradient(135deg, #4a5568, #5a6a82);
    border-left: 6px solid #f39c12;
}

.chat-message .avatar {
    width: 60px;
    height: 60px;
    margin-right: 1rem;
    flex-shrink: 0;
}

.chat-message .avatar img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #fff;
    box-shadow: 0 0 8px rgba(255, 255, 255, 0.4);
    transition: transform 0.3s ease-in-out;
}

.chat-message .avatar img:hover {
    transform: scale(1.1);
}

.chat-message .message {
    flex: 1;
    padding: 0 1rem;
    color: #f0f0f0;
    font-size: 1rem;
    line-height: 1.6;
    font-family: 'Segoe UI', sans-serif;
}
</style>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://images.unsplash.com/photo-1610394212179-8a5bb0c82a0f?auto=format&fit=crop&w=80&q=80" alt="Bot Avatar">
    </div>
    <div class="message">{{MSG}}</div>
</div> '''

user_template = '''
    <div class="chat-message user">
    <div class="avatar">
        <img src="https://images.unsplash.com/photo-1527980965255-d3b416303d12?auto=format&fit=crop&w=80&q=80" alt="User Avatar">
    </div>
    <div class="message">{{MSG}}</div>
</div> '''

