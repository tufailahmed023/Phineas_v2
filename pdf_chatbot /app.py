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

# Import Redis functions with error handling
try:
    from redisdb import get_similar_from_cache, store_in_cache
    REDIS_AVAILABLE = True
except Exception as e:
    # Define placeholder functions if Redis is unavailable
    def get_similar_from_cache(*args, **kwargs):
        return None
    
    def store_in_cache(*args, **kwargs):
        pass
    
    REDIS_AVAILABLE = False
    print(f"Warning: Redis functionality disabled - {str(e)}")

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
    
    try:
        # Track if we're using cache
        is_cache_hit = False
        
        # Check if Redis is available before trying to use it
        if REDIS_AVAILABLE:
            try:
                # 1. Embed the user query using your embedding model
                embedding = st.session_state.embed_model.embed_query(user_question)
                
                # 2. Check Redis cache first
                cached_response = get_similar_from_cache(embedding)
                if cached_response:
                    response_text = cached_response
                    source_docs = []
                    is_cache_hit = True
                    st.session_state.cache_hits = st.session_state.get('cache_hits', 0) + 1
            except Exception as redis_error:
                logger.warning(f"Redis cache error: {str(redis_error)}. Falling back to direct query.")
                cached_response = None
        else:
            cached_response = None
        
        # Proceed with vector search if no cache hit
        if not REDIS_AVAILABLE or not cached_response:
            # 3. Vector Search using ChromaDB
            relevant_docs = retriever.get_relevant_documents(user_question)
            
            # If no relevant docs found, handle gracefully
            if not relevant_docs:
                response_text = "I couldn't find any relevant information in our policies. Please try rephrasing your question or contact HR/IT for assistance."
                source_docs = []
            else:
                context = "\n\n".join([doc.page_content for doc in relevant_docs])
                
                # 4. Build Prompt using prompt engineering
                prompt = build_prompt(
                    user_question, 
                    context, 
                    user_team=st.session_state.get("user_team", "General")
                ) 
                
                # 5. Call LLM
                llm = get_llm()
                response_text = llm.predict(prompt)
                
                # 6. Try to cache result in Redis if available
                if REDIS_AVAILABLE:
                    try:
                        embedding = st.session_state.embed_model.embed_query(user_question)
                        store_in_cache(user_question, response_text, embedding)
                    except Exception as redis_error:
                        logger.warning(f"Failed to store in Redis cache: {str(redis_error)}")
                
                source_docs = relevant_docs
            
            if REDIS_AVAILABLE:
                st.session_state.cache_misses = st.session_state.get('cache_misses', 0) + 1
        
        # 7. Update chat history with new messages
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
            
        st.session_state.chat_history.extend([
            type('Msg', (object,), {'content': user_question}),
            type('Msg', (object,), {'content': response_text})
        ])
        
        # 8. Calculate and optionally log performance metrics
        elapsed_time = time.time() - start_time
        if elapsed_time > 2.0 and not is_cache_hit:
            # Log slow responses for performance monitoring
            logger.warning(f"Slow response ({elapsed_time:.2f}s) for query: {user_question[:50]}...")
        
        # Add performance info to return data
        return {
            'chat_history': st.session_state.chat_history,
            'source_documents': source_docs if 'source_docs' not in locals() else source_docs,
            'response_time': elapsed_time,
            'cache_hit': is_cache_hit
        }
    
    except Exception as e:
        # Handle errors gracefully
        error_msg = f"I'm sorry, I encountered an error processing your request: {str(e)}"
        st.error(error_msg)
        logger.error(f"Error in handle_userinput: {str(e)}", exc_info=True)
        
        # Return a structured error response
        return {
            'chat_history': st.session_state.get('chat_history', []) + [
                type('Msg', (object,), {'content': user_question}),
                type('Msg', (object,), {'content': "I'm sorry, I encountered an error. Please try again or contact support."})
            ],
            'error': str(e),
            'source_documents': []
        }

# --------------------------------------------
def main():
    st.set_page_config(page_title="HR & IT Policy Assistant", page_icon="📋", layout="wide")
    st.write(css, unsafe_allow_html=True)

    # Page Header with better branding
    st.markdown("<h1 style='text-align: center;'>📋 Company Policy Assistant</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>Your HR & IT policy questions answered instantly!</p>", unsafe_allow_html=True)

    # Session state initialization
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.email = ""
    if "embed_model" not in st.session_state:
        # Initialize the embedding model
        st.session_state.embed_model = OllamaEmbeddings(model=model_embedding)

    # Display Redis status in sidebar if there are issues
    if not REDIS_AVAILABLE:
        st.sidebar.warning("⚠️ Redis caching unavailable. Running in fallback mode.")

    # --------------------------------------------
    # LOGIN FORM
    if not st.session_state.logged_in:
        with st.form("login_form"):
            st.markdown("<h3 style='text-align: center;'>Employee Login</h3>", unsafe_allow_html=True)
            email = st.text_input("Enter your company email")
            submitted = st.form_submit_button("Login")
            if submitted:
                if email in user_team_map:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.session_state.user_team = user_team_map[email]
                    st.success(f"Welcome back! You're logged in as {email}")
                    st.rerun()
                else:
                    st.error("Unauthorized email. Please use your company email address.")
        st.stop()

    user_email = st.session_state.email
    user_team = user_team_map[user_email]
    st.session_state.user_team = user_team
    
    # Add team-specific collections with better names
    available_collections = ["Default", user_team]
    selected_collection = st.sidebar.selectbox("Choose collection", available_collections)
    collection_name = selected_collection.replace(" ", "_").lower()

    # --------------------------------------------
    # IMPROVED SIDEBAR UI
    with st.sidebar:
        # st.image("https://via.placeholder.com/150x50.png?text=Company+Logo", width=150)
        st.header(f"Welcome, {user_email.split('@')[0].title()}")
        st.write(f"👤 {user_email}")
        st.write(f"🏷️ Team: {user_team}")
        st.markdown("---")

        st.subheader("📂 Available Policy Documents")
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
            st.markdown("❌ No policy documents available for this selection.")

        st.markdown("---")
        
        # Add helpful tips
        with st.expander("💡 Tips for better results"):
            st.markdown("""
            • Be specific in your questions
            • Mention specific policies when possible
            • For leave questions, specify your employment type
            • For IT questions, mention your device/system
            """)
        
        if st.button("Logout", key="logout_button"):
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
            embedding_function=st.session_state.embed_model,
            persist_directory=persist_directory,
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        st.error(f"Error connecting to vector database: {str(e)}")
        st.info("Please contact IT support or try again later.")
        st.stop()

    # Add session-based conversation display
    if st.session_state.chat_history:
        # Display existing conversation
        for i in range(len(st.session_state.chat_history)):
            if i % 2 == 0:
                st.write(user_template.replace("{{MSG}}", st.session_state.chat_history[i].content), unsafe_allow_html=True)
            else:
                bot_msg = bot_template.replace("{{MSG}}", st.session_state.chat_history[i].content)
                st.write(bot_msg, unsafe_allow_html=True)
    else:
        # First-time user guidance
        st.info("👋 Hello! I'm your HR & IT policy assistant. Ask me any question about company policies.")
        # st.markdown("""
        # **Example questions you can ask:**
        # - How many sick days am I entitled to?
        # - What's the process for requesting work from home?
        # - How do I report an IT security incident?
        # - What's our policy on business travel reimbursement?
        # """)

    # User Input with suggested questions
    user_question = st.text_input("🔍 Ask about any company policy:", key="user_query")
    
    if user_question:
        with st.spinner("Searching policy documents..."):
            response = handle_userinput(user_question, retriever)
            
        # Only show source citation if there are source documents
        if response.get("source_documents"):
            with st.expander("📚 Policy Sources"):
                for i, doc in enumerate(response["source_documents"]):
                    source = doc.metadata.get('source', 'N/A')
                    page = doc.metadata.get('page', 'N/A')
                    st.markdown(f"**Source {i+1}:** `{os.path.basename(source) if source != 'N/A' else 'N/A'}` | **Page:** `{page}`")
                    
                    # Add a preview of the content
                    preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    st.markdown(f"**Preview:** {preview}")
                    st.markdown("---")

    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray;'>Can't find what you need? Contact HR at hr@company.com</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: white;'>@Team Mission Possible : Phineas</p>", unsafe_allow_html=True)

# --------------------------------------------
if __name__ == '__main__':
    main()