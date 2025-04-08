from langchain_chroma import Chroma

def get_vectorstore(collection_name,embedding_function,persist_directory):
    vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=embedding_function,
    persist_directory=persist_directory,)
    return vectorstore