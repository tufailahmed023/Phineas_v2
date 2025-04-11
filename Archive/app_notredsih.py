import streamlit as st
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pdf_utils import model_embedding, persist_directory
from pdf_utils import get_llm
from Templates.htmlTemplates import css, bot_template, user_template
from embedder import log_file, output_folder

# --------------------------------------------
# USER LOGIN CONFIGURATION
user_team_map = {
    "tufail@example.com": "Team A",
    "ahmed@example.com": "Team B",
}

# --------------------------------------------
# IMPROVED PROMPT ENGINEERING
def build_prompt(user_query: str, retrieved_context: str = "", user_team: str = "General") -> str:
    system_prompt = f"""
    You are a professional HR/IT policy assistant for an organization, specifically supporting {user_team}.
    
    Your primary responsibilities:
    - Answer employee queries based ONLY on the company's official HR or IT policies provided in the context
    - NEVER guess, speculate, or make up information
    - If the information isn't available in the policy documents, respond with: "This information is not available in the policy documents. Please contact HR at hr@company.com or IT at support@company.com for assistance."
    - If the question is ambiguous, ask clarifying questions
    - Format responses in a clear, structured way
    - ALWAYS cite the specific policy section when available (e.g., "According to Section 3.2 of the Leave Policy...")
    - Maintain a helpful, professional, and concise tone
    """.strip()
    
    # Enhanced example Q&A with more realistic policy language and better formatting
    example_qna = """
    Example Q&A:
    
    Q: How many leaves can I take in a year?
    A: According to Section 2.1 of the Leave Policy:
    • Full-time employees are entitled to 24 paid leaves annually
    • This includes 12 sick leaves and 12 casual leaves
    • Up to 5 unused leaves can be carried forward to the next year
    • Any additional unused leaves will lapse on December 31st
    
    Q: Can I access my emails while on leave?
    A: According to Section 4.3 of the IT Acceptable Use Policy:
    • Employees are not required to check or respond to emails during approved leave periods
    • For critical roles, an alternative point of contact should be provided before going on leave
    • If you must access work systems during leave, document this time as it may affect your leave balance
    
    Q: What is our policy on remote work?
    A: This information is not available in the policy documents provided. Please contact HR at hr@company.com for the latest remote work policy.
    """.strip()
    
    # Additional conditioning to help with policy interpretation
    policy_guidance = """
    When interpreting policies:
    • Present all relevant conditions and exceptions
    • Include deadlines, limits, and eligibility criteria
    • If the policy has changed recently, note both current and previous versions if available
    • For IT policies, include any security implications
    """.strip()
    
    # Build the full prompt with better structure
    prompt = f"""
    {system_prompt}
    
    {policy_guidance}
    
    {example_qna}
    
    RELEVANT POLICY SECTIONS:
    {retrieved_context or '[No relevant policy sections found in the knowledge base.]'}
    
    USER QUERY:
    {user_query}
    
    RESPONSE:
    """.strip()
    
    return prompt

# --------------------------------------------
# IMPROVED USER INPUT HANDLING WITH CHAT MEMORY
def handle_userinput(user_question, retriever, user_team):
    # Get more relevant documents with an increased k value
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
    prompt = build_prompt(user_question, full_context, user_team)
    
    # Get LLM instance
    llm = get_llm()
    
    # Send the prompt to LLM
    response_text = llm.predict(prompt)
    
    # Add to chat history with proper formatting
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
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
                    st.success(f"Welcome back! You're logged in as {email}")
                    st.rerun()
                else:
                    st.error("Unauthorized email. Please use your company email address.")
        st.stop()

    user_email = st.session_state.email
    user_team = user_team_map[user_email]
    
    # Add team-specific collections with better names
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
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=OllamaEmbeddings(model=model_embedding),
        persist_directory=persist_directory,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

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
    
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     if st.button("📅 Leave policy"):
    #         user_question = "What is our company's leave policy?"
    #         st.session_state.user_query = user_question
    #         st.rerun()
    # with col2:
    #     if st.button("💻 IT security"):
    #         user_question = "What are our IT security policies?"
    #         st.session_state.user_query = user_question
    #         st.rerun()
    # with col3:
    #     if st.button("💼 Travel policy"):
    #         user_question = "What's our business travel policy?"
    #         st.session_state.user_query = user_question
    #         st.rerun()
    
    if user_question:
        with st.spinner("Searching policy documents..."):
            response = handle_userinput(user_question, retriever, user_team)
            
        # Source citation with better formatting
        with st.expander("📚 Policy Sources"):
            for i, doc in enumerate(response["source_documents"]):
                source = doc.metadata.get('source', 'N/A')
                page = doc.metadata.get('page', 'N/A')
                st.markdown(f"**Source {i+1}:** `{os.path.basename(source)}` | **Page:** `{page}`")
                
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