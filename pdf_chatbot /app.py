from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pdf_utils import model_embedding,persist_directory
from pdf_utils import get_llm,get_conversation_chain
from Templates.htmlTemplates import css, bot_template, user_template
from embedder import log_file,output_folder
import streamlit as st
import os



def handle_userinput(user_question,retriever):
    st.session_state.qa_chain = get_conversation_chain(retriever=retriever,llm=get_llm())
    response = st.session_state.qa_chain({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    # Display the conversation
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            bot_msg = bot_template.replace("{{MSG}}", message.content)
            st.write(bot_msg, unsafe_allow_html=True)
    return response




def main():
    # Set page title and icon
    st.set_page_config(page_title="Chat with Your PDFs 📚", page_icon="📖", layout="wide")

    # Apply custom CSS (if any)
    st.write(css, unsafe_allow_html=True)

    # Page Header
    st.markdown("<h1 style='text-align: center;'>📖 Chat with Your PDFs 📖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>Ask anything about your uploaded documents!</p>", unsafe_allow_html=True)

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "qa_chain" not in st.session_state:
        st.session_state.qa_chain = None
    
    st.sidebar.header("Select Team")
    available_collections = ["Team A", "Team B"]
    selected_collection = st.sidebar.selectbox("Choose collection", available_collections)
    collection_name = selected_collection.replace(" ", "_").lower()

    

    # Sidebar Section
    st.sidebar.title("📂 Processed PDFs")
    pdf_list_path = os.path.join(os.curdir, output_folder, f"{collection_name}_{log_file}")
    


    if os.path.exists(pdf_list_path):
        with open(pdf_list_path, "r") as file:
            pdf_files = file.readlines()
        pdf_files = [pdf.strip() for pdf in pdf_files if pdf.strip()]  # Remove empty lines
    else:
        pdf_files = []

    if pdf_files:
        for pdf in pdf_files:
            st.sidebar.markdown(f"✅ {pdf}")
    else:
        st.sidebar.markdown("❌ No PDFs processed yet.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("📌 **Happy Analyzing :) **")

  

    # Vector Store Initialization
    vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=OllamaEmbeddings(model=model_embedding),
    persist_directory=persist_directory,)

    retriever = vectorstore.as_retriever(search_kwargs={"k":1})


    # User Input
    user_question = st.text_input("🔍 Ask a question:")
    if user_question:
        responce = handle_userinput(user_question,retriever)
        with st.expander("📚 Source Details"):
            for i, doc in enumerate(responce["source_documents"]):
                st.markdown(f"📄 **Source:** `{doc.metadata.get('source', 'N/A')}` | 📄 **Page:** `{doc.metadata.get('page', 'N/A')}`")
                st.markdown("---")

    # Footer Note
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray;'>💡 Tip: Upload multiple PDFs and get instant insights!</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: white;'> @Team Mission Possiable : Phineas </p>", unsafe_allow_html=True)


if __name__ == '__main__':
    main()