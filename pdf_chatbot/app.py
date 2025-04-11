import streamlit as st
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pdf_utils import model_embedding, persist_directory
from pdf_utils import get_llm, get_conversation_chain, build_prompt
from Templates.htmlTemplates import css, bot_template, user_template,get_base64_image
from embedder import log_file, output_folder
from PIL import Image
from io import BytesIO
from PIL import Image
import os



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
        background-color: #fffaf5;
        color: #4e3b31;
    }

    .stApp {
        padding: 40px;
        background-color: #fffaf5;
    }

    h1, h2, h3 {
        font-family: 'Cirka', serif;
        color: #5a3e36;
        margin-bottom: 0.4em;
    }

    .stTextInput input {
        background-color: #fff;
        color: #4e3b31;
        border: none;
        border-bottom: 2px solid #e8c1a0;
        border-radius: 0;
        padding: 0.6em;
    }

    .stButton button {
        background-color: #f4c29c;
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }

    .stButton button:hover {
        background-color: #e7a97e;
    }

    .stSidebar {
        background-color: #fff3e6;
        padding: 20px;
    }

    .stSidebar h1, .stSidebar h2 {
        color: #7a5548;
    }

    .stSidebar div, .stSidebar p {
        color: #5f4339;
        font-size: 15px;
    }

    .stExpander {
        background-color: #fef6f1;
        border: none;
        border-radius: 10px;
        padding: 10px;
    }

    hr {
        border: none;
        border-top: 1px dashed #e8c1a0;
        margin: 30px 0;
    }

    .phineas-icon {
        display: block;
        margin: 0 auto 20px auto;
        width: 90px;
        border-radius: 12px;
    }

    .chat-container {
        padding: 10px 0;
        margin-top: 20px;
    }

    .genz-tagline {
        text-align: center;
        font-size: 14px;
        color: #b5765b;
        font-style: italic;
        margin-top: 5px;
        letter-spacing: 0.3px;
    }

    .genz-fill-space {
        height: 12px;
        background: linear-gradient(90deg, #fff4ec 0%, #ffeedd 100%);
        margin: 20px 0;
        border-radius: 8px;
    }

    .stSelectbox div[data-baseweb="select"] {
        background-color: #fff;
        border: none;
        border-bottom: 2px solid #eac9b0;
        border-radius: 0;
        font-family: 'Gilroy';
    }

</style>
""", unsafe_allow_html=True)

    # st.markdown(f'<img src= {Image.open(BytesIO(logo))} class="phineas-icon" alt="Phineas Icon">', unsafe_allow_html=True)
   
    st.write(css, unsafe_allow_html=True)

    # Page Header
    st.markdown("<h1 style='text-align: center;'>Phineas 🤖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>No more digging through PDFs. Just ask.</p>", unsafe_allow_html=True)
    st.markdown("<div class='genz-tagline'>✨ Powered by vibes, built with brains ✨</div>", unsafe_allow_html=True)
    st.markdown("<div class='genz-fill-space'></div>", unsafe_allow_html=True)


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
    st.markdown("<p style='text-align: center; font-size: 14px; color: dark gray;'>💡 Tip: Ask smart. Get sharp answers 🧠 </p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: black;'> @Team Mission Possible : Phineas </p>", unsafe_allow_html=True)


# --------------------------------------------
if __name__ == '__main__':
    main()