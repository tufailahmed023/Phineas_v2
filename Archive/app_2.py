import streamlit as st
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pdf_utils import model_embedding, persist_directory
from pdf_utils import get_llm, get_conversation_chain
from Templates.htmlTemplates import css, bot_template, user_template
from embedder import log_file, output_folder

# --------------------------------------------
# USER LOGIN CONFIGURATION
user_team_map = {
    "tufail@example.com": "Team A",
    "ahmed@example.com": "Team B",
}
#-------------------------------------------------
def build_prompt(user_query: str, retrieved_context: str = "") -> str:
    system_prompt = """

        You are a professional HR/IT policy assistant for an organization.
        Answer employee queries clearly and only based on the company’s official HR or IT policies.
        Do not guess or hallucinate. If the answer is not available in the policy, respond with:
        "This is not available in the policy documents."
        Provide your answer in a simple, helpful, and professional tone.
        If the policy includes dates, limits, or conditions — include those in the response.
        Use bullet points if multiple conditions apply.
    """.strip()
    example_qna = """
    Example Q&A:
    Q: How many leaves can I take in a year?
    A: 
    - According to the HR leave policy, you are entitled to 24 paid leaves annually.
    - This includes sick and casual leaves.
    - Any unused leaves beyond the carry-forward limit will lapse.
    Q: Can I access my emails while on leave?
    A: The IT policy does not recommend checking official emails during approved leave periods unless required in critical cases.
        """.strip()
    prompt = f"""
                {system_prompt}
                {example_qna}
                Relevant Policy Snippets:
                {retrieved_context or '[No relevant policy snippets found.]'}
                User Query:
                {user_query}
                Answer:
                """.strip()
    return prompt



def handle_userinput(user_question, retriever):
    # Embed the user query using your nomic-embed-text model
    embedding = st.session_state.embed_model.embed(user_question)
    # 1. Check Redis cache
    cached_response = get_similar_from_cache(embedding)
    if cached_response:
        response_text = cached_response
        source_docs = []
    else:
        # 2. Vector Search using ChromaDB
        relevant_docs = retriever.get_relevant_documents(user_question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        # 3. Build Prompt using prompt engineering
        prompt = build_prompt(user_question, context) 
        # 4. Call LLM
        llm = get_llm()
        response_text = llm.predict(prompt)

        # 5. Cache new result in Redis
        store_in_cache(user_question, response_text, embedding)

        source_docs = relevant_docs
 
    # 6. Simulate chat display

    st.session_state.chat_history = [
        type('Msg', (object,), {'content': user_question}),
        type('Msg', (object,), {'content': response_text})
    ]
 
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True) 
    return {
        'chat_history': st.session_state.chat_history,
        'source_documents': source_docs
    }

 

 

# --------------------------------------------
def main():
    st.set_page_config(page_title="Chat with Your PDFs 📚", page_icon="📖", layout="wide")
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
