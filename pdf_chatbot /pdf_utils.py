
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

from vectordb import get_vectorstore


model_embedding ="nomic-embed-text:latest"
model_llm = 'llama3.2:3b'
collection_name="pdfs"
persist_directory = os.path.join('.', 'chroma_db')  # Change this to your desired path


def get_pdf_text_emd(pdf_path, log_file="processed_pdfs.txt", output_folder="extracted_texts"):

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


def get_llm(): 
    llm = OllamaLLM(model=model_llm, temperature=0.1, max_tokens=1000)
    return llm 


def get_conversation_chain(retriever,llm):
    
    memory = ConversationBufferMemory(
                        memory_key='chat_history', 
                        return_messages=True,
                        input_key='question',    
                        output_key='answer')
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        output_key="answer"
    )
    return conversation_chain

