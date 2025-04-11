import streamlit as st
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pdf_utils import model_embedding, persist_directory
from pdf_utils import get_llm, get_conversation_chain, build_prompt
from Templates.htmlTemplates import css, bot_template, user_template
from embedder import log_file, output_folder

# --------------------------------------------
# USER LOGIN CONFIGURATION
user_team_map = {
    "tufail@example.com": "Team A",
    "ahmed@example.com": "Team B",
    "a" : ["Team A", "Team B"]
}

# --------------------------------------------
def handle_userinput(user_question, retriever):
    relevant_docs = retriever.get_relevant_documents(user_question, k=3)
    
    # Process and filter contexts for relevance
    contexts = []
    sources = []
    
    for doc in relevant_docs:
        # Extract metadata
        source = doc.metadata.get('source', 'Unknown source')
        page = doc.metadata.get('page', 'Unknown page')
        
        # Add source info to context
        context_with_source = f"[From: {os.path.basename(source)}, Page: {page}]\n{doc.page_content}"
        contexts.append(context_with_source)
        sources.append(f"{os.path.basename(source)}, Page: {page}")
    
    # Join all contexts with clear separators
    full_context = "\n\n---\n\n".join(contexts)
    
    # Build the prompt using enhanced prompt engineering
    prompt = build_prompt(user_question, full_context)
    
    # Get LLM instance
    llm = get_llm()
    
    # Send the prompt to LLM
    response_text = llm.predict(prompt)
    
    # Add current Q&A to history
    st.session_state.chat_history.extend([
        type('Msg', (object,), {'content': user_question}),
        type('Msg', (object,), {'content': response_text})
    ])
    
    # Keep only the last 6 messages (3 exchanges) for context
    if len(st.session_state.chat_history) > 6:
        st.session_state.chat_history = st.session_state.chat_history[-6:]
    
    # Display the most recent conversation
    for i in range(len(st.session_state.chat_history)):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", st.session_state.chat_history[i].content), unsafe_allow_html=True)
        else:
            bot_msg = bot_template.replace("{{MSG}}", st.session_state.chat_history[i].content)
            st.write(bot_msg, unsafe_allow_html=True)

    return {
        'chat_history': st.session_state.chat_history,
        'source_documents': relevant_docs,
        'sources': sources
    }

# --------------------------------------------
def main():
    # Streamlit page configuration
    st.set_page_config(page_title="Chat with Your PDFs 📚", page_icon="📖", layout="wide")
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Overpass+Mono&display=swap');
    @font-face {
        font-family: 'Gilroy';
        src: url('https://fonts.cdnfonts.com/s/14845/Gilroy-Light.woff') format('woff');
    }
    @font-face {
        font-family: 'Cirka';
        src: url('https://fonts.cdnfonts.com/s/14571/Cirka-Regular.woff') format('woff');
    }

    html, body, [class*="css"] {
        font-family: 'Gilroy', 'Overpass Mono', sans-serif;
        background: linear-gradient(135deg, #121212, #1c1c1c);
        color: #e0e0e0;
    }

    .stApp {
        width: 100%;
        padding: 30px;
    }

    h1, h2, h3 {
        font-family: 'Cirka', serif;
        color: #ffffff;
    }

    .stTextInput input {
        background-color: #202020;
        color: #ffffff;
        border-radius: 8px;
        border: 1px solid #444;
        padding: 0.6em;
    }

    .stButton button {
        background-color: #292929;
        color: #ffffff;
        border: 1px solid #555;
        border-radius: 8px;
        transition: all 0.2s ease;
        padding: 0.5em 1.2em;
    }

    .stButton button:hover {
        background-color: #333;
        border-color: #777;
    }

    .stSidebar, .stMarkdown, .stExpander {
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 10px;
    }

    hr {
        border: none;
        border-top: 1px solid #444;
        margin-top: 2em;
        margin-bottom: 2em;
    }

    img.phineas-icon {
        display: block;
        margin: 0 auto 20px auto;
        width: 100px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)
    st.markdown('<img src="pdf_chatbot /Images/Profile_-_Phineas_Flynn.PNG.webp" class="phineas-icon" alt="Phineas Icon">', unsafe_allow_html=True)
    st.write(css, unsafe_allow_html=True)

    # Page Header
    st.markdown("<h1 style='text-align: center;'>📖 Chat with Your PDFs 📖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>Ask anything about your uploaded documents!</p>", unsafe_allow_html=True)

    # Session state init
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "qa_chain" not in st.session_state:
        st.session_state.qa_chain = None
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.email = ""

    # --------------------------------------------
    # LOGIN FORM
    if not st.session_state.logged_in:
        with st.form("login_form"):
            email = st.text_input("Enter your email")
            submitted = st.form_submit_button("Login")
            if submitted:
                if email in user_team_map:
                    st.session_state.logged_in = True
                    st.session_state.email = email
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Unauthorized email.")
        st.stop()

    user_email = st.session_state.email
    user_team = user_team_map[user_email]
    available_collections = ["Default", user_team]
    selected_collection = st.sidebar.selectbox("Choose collection", available_collections)
    collection_name = selected_collection.replace(" ", "_").lower()

    # --------------------------------------------
    # SIDEBAR UI
    st.sidebar.header("Welcome")
    st.sidebar.write(f"👤 {user_email}")
    st.sidebar.write(f"🏷️ Team: {user_team}")
    st.sidebar.markdown("---")

    st.sidebar.title("📂 Processed PDFs")
    pdf_list_path = os.path.join(os.curdir, output_folder, f"{collection_name}_{log_file}")

    if os.path.exists(pdf_list_path):
        with open(pdf_list_path, "r") as file:
            pdf_files = [pdf.strip() for pdf in file if pdf.strip()]
    else:
        pdf_files = []

    if pdf_files:
        for pdf in pdf_files:
            st.sidebar.markdown(f"✅ {pdf}")
    else:
        st.sidebar.markdown("❌ No PDFs processed yet.")

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.email = ""
        st.rerun()

    # --------------------------------------------
    # Vector Store (team-specific)
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=OllamaEmbeddings(model=model_embedding),
        persist_directory=persist_directory,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})

    # --------------------------------------------
    # User Input
    user_question = st.text_input("🔍 Ask a question:")
    if user_question:
        response = handle_userinput(user_question, retriever)
        with st.expander("📚 Source Details"):
            for i, doc in enumerate(response["source_documents"]):
                st.markdown(f"📄 **Source:** `{doc.metadata.get('source', 'N/A')}` | 📄 **Page:** `{doc.metadata.get('page', 'N/A')}`")
                st.markdown("---")

    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray;'>💡 Tip: Upload multiple PDFs and get instant insights!</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: white;'> @Team Mission Possible : Phineas </p>", unsafe_allow_html=True)

# --------------------------------------------
if __name__ == '__main__':
    main()