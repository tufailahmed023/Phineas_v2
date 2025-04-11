
import os
import sys 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_ollama.llms import OllamaLLM
from langchain.prompts import PromptTemplate


from vectordb import get_vectorstore,pdf_file_path


model_embedding ="nomic-embed-text:latest"
model_llm = 'llama3.2:3b'
collection_name= os.path.basename(pdf_file_path).lower()
persist_directory = os.path.join('.', 'chroma_db')  # Change this to your desired path


def get_pdf_text_emd(pdf_path, log_file="processed_pdfs.txt", output_folder="extracted_texts"):

    log_file = f'{collection_name}_{log_file}'

    output_folder_path = os.path.join(os.path.abspath(os.curdir),output_folder)
    if os.path.exists(output_folder_path) == False :
        os.makedirs(output_folder_path)

    # Read the log file to track already processed PDFs
    processed_pdfs = set()
    log_file_path = os.path.join(output_folder_path, log_file)  # Fix path issue

    if os.path.exists(log_file_path):
        with open(log_file_path, "r") as f:
            processed_pdfs.update(f.read().splitlines())

    # Get list of PDF files to process
    pdf_files = []
    if os.path.isdir(pdf_path):  # If a folder is given
        pdf_files = [os.path.join(pdf_path, f) for f in os.listdir(pdf_path) if f.endswith(".pdf")]
    elif os.path.isfile(pdf_path) and pdf_path.endswith(".pdf"):  # If a single PDF file is given
        pdf_files = [pdf_path]
    else:
        print(f"Invalid path: {pdf_path}")
        return None  # Return None for invalid input

    

    for pdf_file in pdf_files:
        pdf_name = os.path.basename(pdf_file)
        
        if pdf_name in processed_pdfs:
            print(f"Skipping already processed PDF: {pdf_name}")
            continue  # Skip already processed files

        print(f"Processing: {pdf_name}")
    

        try:
            loader = PyPDFLoader(pdf_file) or ""  # Handle NoneType cases
            documents = loader.load() or []
        
            with open(log_file_path, "a") as f:
                f.write(pdf_name + "\n")

        except Exception as e:
            print(f"Error processing {pdf_name}: {e}")

        print("Creating Chuncks.")
        text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200,
                        separators=["\n\n", "\n", ".", "?", "!", " ", ""],
                        length_function=len)
        # Split the text into chunks
        chunks = text_splitter.split_documents(documents)

        print("Creating embeddings .")
        # Create embeddings
        embeddings = OllamaEmbeddings(model=model_embedding)
        # Create a Chroma vector store
        vectorstore = get_vectorstore(collection_name=collection_name, embedding_function=embeddings, 
                                       persist_directory=persist_directory) 
        # Add the chunks to the vector store
        documents,ids = [], [] 
        for idx, split in enumerate(chunks):
            split.metadata['source'] = pdf_name
            document = Document(
            page_content=split.page_content,
            metadata=split.metadata)

            documents.append(document)
            ids.append(f"{split.metadata['source']}_{idx}")
        # Add documents to the vector store
        print("Adding documents to vectorstore.")
        vectorstore.add_documents(documents, ids=ids)
    

    print("PDF processing and  completed.")
    return 


def get_llm(temperature = 0.1): 
    llm = OllamaLLM(model=model_llm,
                    temperature=temperature,  # Lower for more factual responses
                    repeat_penalty=1.1,       # Discourage repetition
                    top_k=40,                 # Consider more token possibilities
                    top_p=0.95,               # Sample from more probable tokens
                    num_ctx=4096)              # Larger context window for better understanding)
    return llm 


# def get_conversation_chain(retriever,llm):
    
    # memory = ConversationBufferMemory(
    #                     memory_key='chat_history', 
    #                     return_messages=True,
    #                     input_key='question',    
    #                     output_key='answer')
    
    # conversation_chain = ConversationalRetrievalChain.from_llm(
    #     llm=llm,
    #     retriever=retriever,
    #     memory=memory,
    #     return_source_documents=True,
    #     output_key="answer"
    # )
    # return conversation_chain

def get_conversation_chain(retriever, llm):
    """Create a conversation chain with enhanced prompt template and memory"""
    # Create an improved prompt template
    prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history"],
    )
    
    # Create a memory buffer that retains conversation context
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # Create the conversation chain with the improved components
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt},
        return_source_documents=True,
        verbose=True
    )

def build_prompt(user_query: str, retrieved_context: str = "") -> str:
    system_prompt = f"""
    You are a professional HR/IT policy assistant for an organization.
    
    Your primary responsibilities:
    - Answer employee queries based ONLY on the company's official HR or IT policies provided in the context
    - NEVER guess, speculate, or make up information
    - If the information isn't available in the policy documents, respond with: "This information is not available in the policy documents. Please contact HR at hr@company.com or IT at support@company.com for assistance."
    - If the question is ambiguous, ask clarifying questions
    - Format responses in a clear, structured way
    - ALWAYS cite the specific policy section when available (e.g., "According to Section 3.2 of the Leave Policy...")
    - Maintain a helpful, professional, and concise tone
    - Do not assign any full form for abbreviations on your own, always refer to data or ask the user back for clarification.
    - Only answer for the given question and its context, even though it applies to other areas well. Always answer the asked question and do not add additional information in the question
    """.strip()
    
    # Enhanced example Q&A with more realistic policy language and better formatting
    example_qna = """
    Example Q&A:
    
    Q: Can I access my emails while on leave?
    A: According to the IT Acceptable Use Policy:
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