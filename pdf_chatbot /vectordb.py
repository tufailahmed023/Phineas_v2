from langchain_chroma import Chroma

# pdf_file_path = '/Users/tufailahmed/Desktop/PDFs/Team_A'
# pdf_file_path = '/Users/tufailahmed/Desktop/PDFs/Team_B'
pdf_file_path = '/Users/tufailahmed/Desktop/PDFs/Default'



def get_vectorstore(collection_name,embedding_function,persist_directory):
    vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=embedding_function,
    persist_directory=persist_directory,)
    return vectorstore