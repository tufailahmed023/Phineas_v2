import streamlit as st
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pdf_utils import model_embedding, persist_directory
from pdf_utils import get_llm,build_prompt
from Templates.htmlTemplates import css, bot_template, user_template
from embedder import log_file, output_folder
import time
import logging


# Setup logging
logger = logging.getLogger(__name__)

# --------------------------------------------
# USER LOGIN CONFIGURATION
user_team_map = {
    "tufail@example.com": "Team A",
    "ahmed@example.com": "Team B",
}

# --------------------------------------------
# IMPROVED USER INPUT HANDLING WITH CHAT MEMORY
def handle_userinput(user_question, retriever):
    start_time = time.time()
    

    # Initialize source_docs to avoid the UnboundLocalError
    source_docs = []
    
    # 3. Vector Search using ChromaDB
    relevant_docs = retriever.get_relevant_documents(user_question)
    
    if not relevant_docs:
        response_text = "I couldn't find any relevant information in our policies. Please try rephrasing your question or contact HR/IT for assistance."
        # source_docs is already initialized as an empty list
    else:
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # 4. Build Prompt using prompt engineering
        prompt = build_prompt(
            user_question, 
            context, 
        ) 
        
        # 5. Call LLM
        llm = get_llm()
        response_text = llm.predict(prompt)
        
        # Set source_docs to relevant_docs
        source_docs = relevant_docs
    
    # 7. Update chat history with new messages
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    st.session_state.chat_history.extend([
        type('Msg', (object,), {'content': user_question}),
        type('Msg', (object,), {'content': response_text})
    ])
    
    # 8. Calculate and optionally log performance metrics
    elapsed_time = time.time() - start_time
    if elapsed_time > 2.0 :
        # Log slow responses for performance monitoring
        logger.warning(f"Slow response ({elapsed_time:.2f}s) for query: {user_question[:50]}...")
    
    # Add performance info to return data
    return {
        'chat_history': st.session_state.chat_history,
        'source_documents': source_docs,  # Now source_docs is always defined
        'response_time': elapsed_time,
    }

# --------------------------------------------
def main():
    st.set_page_config(page_title="HR & IT Policy Assistant", page_icon="📋", layout="wide")
    st.markdown('''
    <style>
        body {
            background-color: #121212;
            color: #f5f5f5;
        }
        .stApp {
            background-color: #121212;
        }
        h1, h3, p {
            color: #f5f5f5 !important;
        }
        .css-1d391kg, .css-1v0mbdj, .css-1kyxreq {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
        }
        a {
            color: #00aaff !important;
        }
    </style>''', unsafe_allow_html=True)
    st.markdown('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #111111;
        color: #eeeeee;
    }

    .stApp {
        max-width: 840px;
        margin: auto;
        padding-top: 30px;
    }

    h1 {
        font-size: 44px;
        font-weight: 700;
        color: #ffffff;
        text-align: center;
        margin-bottom: 6px;
    }

    h3 {
        font-size: 24px;
        font-weight: 500;
        text-align: center;
        color: #cccccc;
    }

    p, label {
        color: #cccccc !important;
        font-size: 16px;
    }

    .stTextInput input {
        background-color: #1b1b1b;
        color: #f0f0f0;
        border-radius: 10px;
        border: 1px solid #333;
        padding: 0.6em;
    }

    .stButton button {
        background-color: #222;
        color: #f9f9f9;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        border: 1px solid #444;
        font-weight: 500;
        transition: all 0.25s ease;
    }

    .stButton button:hover {
        background-color: #2d2d2d;
        transform: scale(1.03);
        border-color: #666;
    }

    .stMarkdown hr {
        border: none;
        border-top: 1px solid #444;
        margin-top: 2em;
        margin-bottom: 1em;
    }

    .stExpanderHeader {
        color: #ffffff;
        font-weight: 600;
    }

    img {
        display: block;
        margin: 0 auto 20px auto;
        border-radius: 14px;
    }
</style>
''', unsafe_allow_html=True)
    st.markdown('''
<div style='text-align: center; margin-top: 10px;'>
    <img src='https://upload.wikimedia.org/wikipedia/en/thumb/e/e7/Phineas_Flynn.png/220px-Phineas_Flynn.png' 
         width='100' alt='Phineas Icon'>
</div>
''', unsafe_allow_html=True)
    st.write(css, unsafe_allow_html=True)

    # Page Header with better branding
    st.markdown("<h1 style='text-align: center; font-size: 42px; font-weight: bold; color: #2c3e50;'>🌐 Phineas</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 20px; color: #34495e;'>Got Qs? I’ve got the tea on HR & IT 🍵💼</p>", unsafe_allow_html=True)

    # Session state initialization
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.email = ""




    # --------------------------------------------
    # LOGIN FORM
    if not st.session_state.logged_in:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center;'>🔐 Employee 🚀 Login</h3>", unsafe_allow_html=True)
            email = st.text_input("📧 Enter yur organization email")
            submitted = st.form_submit_button("🚀 Login")
            if submitted:
                if email in user_team_map:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.success(f"Welcome back! You're logged in as {email}")
                    st.rerun()
                else:
                    st.error("❌ Unauthorized email. Use your work email, fam.")
        st.stop()

    user_email = st.session_state.email
    user_team = user_team_map[user_email]

    
    # Add team-specific collections with better names
    available_collections = ["Default", user_team]
    selected_collection = st.sidebar.selectbox("Choose collection", available_collections)
    collection_name = selected_collection.replace(" ", "_").lower()

    # --------------------------------------------
    # IMPROVED SIDEBAR UI
    with st.sidebar:
        # st.image("https://via.placeholder.com/150x50.png?text=Company+Logo", width=150)
        st.header(f"👋 Hey there, {user_email.split('@')[0].title()}")
        st.write(f"👤 {user_email}")
        st.write(f"🏷️ Team: {user_team}")
        st.markdown("---")

        st.subheader("📁 Your Policy Files")
        pdf_list_path = os.path.join(os.curdir, output_folder, f"{collection_name}_{log_file}")

        if os.path.exists(pdf_list_path):
            with open(pdf_list_path, "r") as file:
                pdf_files = [pdf.strip() for pdf in file if pdf.strip()]
        else:
            pdf_files = []

        if pdf_files:
            for pdf in pdf_files:
                st.markdown(f"✅ {pdf}")
        else:
            st.markdown("🛑 No docs found. Ping HR maybe?")

        st.markdown("---")
        
        # Add helpful tips
        with st.expander("💡 Ask like a pro"):
            st.markdown("""
            🔹 Be clear, not cryptic
            🔹 Drop policy names if you can
            🔹 Mention your role/type if relevant
            🔹 For IT stuff, tell me your device/system
            """)
        
        if st.button("🚪 Log me out", key="logout_button"):
            st.session_state.logged_in = False
            st.session_state.email = ""
            st.session_state.chat_history = []
            st.rerun()

    # --------------------------------------------
    # MAIN CONTENT AREA
    
    # Vector Store (team-specific)
    try:
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=OllamaEmbeddings(model=model_embedding),
            persist_directory=persist_directory,
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        st.error(f"Error connecting to vector database: {str(e)}")
        st.info("Please contact IT support or try again later.")
        st.stop()

    # Add session-based conversation display
    # if st.session_state.chat_history:
    #     # Display existing conversation
    #     for i in range(len(st.session_state.chat_history)):
    #         if i % 2 == 0:
    #             st.write(user_template.replace("{{MSG}}", st.session_state.chat_history[i].content), unsafe_allow_html=True)
    #         else:
    #             bot_msg = bot_template.replace("{{MSG}}", st.session_state.chat_history[i].content)
    #             st.write(bot_msg, unsafe_allow_html=True)
    # for i, message in enumerate(st.session_state.chat_history):
    #     if i % 2 == 0:
    #         st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
    #     else:
    #         st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True) 
    # return {
    #     'chat_history': st.session_state.chat_history,
    #     'source_documents': source_docs
    # }
    if st.session_state.chat_history:
        for i in range(len(st.session_state.chat_history)):
            role = "🧑 You" if i % 2 == 0 else "🤖 Phineas"
            st.markdown(f"**{role}:** {st.session_state.chat_history[i].content}")
    else:
        st.info("🤖 Yo! I’m Phineas — your HR/IT chatbot. Ask away, I don’t judge.")

    # else:
    #     # First-time user guidance
    #     st.info("🤖 Yo! I’m Phineas — your HR/IT chatbot. Ask away, I don’t judge.")
    #     # st.markdown("""
    #     # **Example questions you can ask:**
    #     # - How many sick days am I entitled to?
    #     # - What's the process for requesting work from home?
    #     # - How do I report an IT security incident?
    #     # - What's our policy on business travel reimbursement?
    #     # """)

    # User Input with suggested questions
    user_question = st.text_input("💬 Ask me anything about company policies...", key="user_query")
    
    if user_question:
        with st.spinner("🔍 Searching the policy vault..."):
            response = handle_userinput(user_question, retriever)
            
        # Only show source citation if there are source documents
        if response.get("source_documents"):
            with st.expander("📚 Sources I checked"):
                for i, doc in enumerate(response["source_documents"]):
                    source = doc.metadata.get('source', 'N/A')
                    page = doc.metadata.get('page', 'N/A')
                    st.markdown(f"📄 Source {i+1}: `{os.path.basename(source) if source != 'N/A' else 'N/A'}` | 📎 Page: `{page}`")
                    
                    # Add a preview of the content
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    st.markdown(f"🔍 Preview: {preview}")
                    st.markdown("---")

    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 16px; color: gray;'>🙋 Still stuck? HR’s got your back → <a href='mailto:hr@company.com' style='color: #2980b9;'>hr@company.com</a></p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: #7f8c8d;'>🎯 Built with love by <strong>Team Mission Possible: Phineas</strong></p>", unsafe_allow_html=True)

# --------------------------------------------
if __name__ == '__main__':
    main()