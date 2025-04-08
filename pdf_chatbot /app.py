from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pdf_utils import model_embedding,persist_directory,collection_name
from pdf_utils import get_llm,get_conversation_chain
from Templates.htmlTemplates import css, bot_template, user_template
import streamlit as st
import os

vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=OllamaEmbeddings(model=model_embedding),
    persist_directory=persist_directory,)

retriever = vectorstore.as_retriever(search_kwargs={"k":1})

# def get_answer(query):
#     llm = get_llm()
#     chain = RetrievalQA.from_chain_type(
#         llm=llm,
#         chain_type="stuff",
#         retriever=retriever,
#         return_source_documents=True,
#     )
#     response = chain({"query": query})
#     answer = response["result"]
#     source_documents = response["source_documents"]
    
#     return answer, source_documents

# if "conversation" not in st.session_state:
#         st.session_state.conversation = None
# if "chat_history" not in st.session_state:
#         st.session_state.chat_history = None

# user_question = st.text_input("🔍 Ask a question:")

# st.session_state.conversation = get_conversation_chain(retriever=retriever, llm=get_llm())
# response = st.session_state.conversation({'question': user_question})
# st.session_state.chat_history = response['chat_history']



def handle_userinput(user_question):
    st.session_state.qa_chain = get_conversation_chain(retriever=retriever,llm=get_llm())
    response = st.session_state.qa_chain({'question': user_question})
    st.session_state.chat_history = response['chat_history']
#     # Get the conversation chain and generate a response
#     # Extract sources if available
    # sources = ""
    # pages = ''
    
    # if "source_documents" in response:
    #     source_list = []
    #     page_list = []
    #     for doc in response["source_documents"]:
    #         if hasattr(doc, 'metadata') and 'source' in doc.metadata:
    #             source_list.append(doc.metadata['source'])
    #             page_list.append(doc.metadata['page'])
    #     if source_list:
    #         sources =  ",".join(src for src in set(source_list)) 
    #         pages = ",".join(page for page in set(page_list)) 

    # Display the conversation
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            bot_msg = bot_template.replace("{{MSG}}", message.content)
            # Only show sources and pages for the **last message**
            # if i == len(st.session_state.chat_history) - 1:
            #     bot_msg = bot_msg.replace("{{SRC}}", sources)
            #     bot_msg = bot_msg.replace("{{page}}", pages)
            # else:
            #     bot_msg = bot_msg.replace("{{SRC}}", "")
            #     bot_msg = bot_msg.replace("{{page}}", "")
            st.write(bot_msg, unsafe_allow_html=True)
    return response




def main():
    # Set page title and icon
    st.set_page_config(page_title="Chat with Your PDFs 📚", page_icon="📖", layout="wide")

    # Apply custom CSS (if any)
    st.write(css, unsafe_allow_html=True)

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "qa_chain" not in st.session_state:
        st.session_state.qa_chain = None

    # Sidebar Section
    st.sidebar.title("📂 Processed PDFs")
    pdf_list_path = "extracted_texts/processed_pdfs.txt"

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

    # Page Header
    st.markdown("<h1 style='text-align: center;'>📖 Chat with Your PDFs 📖</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>Ask anything about your uploaded documents!</p>", unsafe_allow_html=True)



    # st.session_state.qa_chain = get_conversation_chain(retriever=retriever, llm=get_llm())

    # if st.session_state.qa_chain:
    #     user_input = st.text_input("Ask something about the PDF:")
    #     if user_input:
    #         result = st.session_state.qa_chain({"question": user_input})

    #         # Update chat history
    #         st.session_state.chat_history.append(("You", user_input))
    #         st.session_state.chat_history.append(("Bot", result["answer"]))

    #         # Display chat
    #         for role, msg in st.session_state.chat_history:
    #             st.chat_message(role).markdown(msg)

            # print(result.keys())

            # Show source docs & metadata


    # User Input
    user_question = st.text_input("🔍 Ask a question:")
    if user_question:
        responce = handle_userinput(user_question)
        with st.expander("📚 Source Details"):
            for i, doc in enumerate(responce["source_documents"]):
                st.markdown(f"📄 **Source:** `{doc.metadata.get('source', 'N/A')}` | 📄 **Page:** `{doc.metadata.get('page', 'N/A')}`")
                st.markdown("---")

    # Footer Note
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: gray;'>💡 Tip: Upload multiple PDFs and get instant insights!</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: white;'> @Team Mission Possiable : Phineas </p>", unsafe_allow_html=True)



# answer , source_documents = get_answer("What is the purpose of this document?")
# source = []
# page = []
# for doc in source_documents:
#     source.append(doc.metadata['source'])
#     page.append(doc.metadata['page'])
    
# print("Answer :",answer)
# print(f"The Source {set(source)} and pages {set(page)}")

if __name__ == '__main__':
    main()