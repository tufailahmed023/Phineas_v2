from langchain_chroma import Chroma
import redis
import numpy as np
import json

# pdf_file_path = '/Users/tufailahmed/Desktop/PDFs/Team_A'
# pdf_file_path = '/Users/tufailahmed/Desktop/PDFs/Team_B'
pdf_file_path = '/Users/tufailahmed/Desktop/PDFs/Default'



def get_vectorstore(collection_name,embedding_function,persist_directory):
    vectorstore = Chroma(
    collection_name=collection_name,
    embedding_function=embedding_function,
    persist_directory=persist_directory,)
    return vectorstore

def redis_client():
    # Connect to Redis (adjust host/port if needed)
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    return redis_client