# Add this to your pdf_utils.py file or create a new prompt_engineering.py file

from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import Ollama
import os

# Improved system prompt with clear instructions for the LLM
SYSTEM_TEMPLATE = """You are an intelligent assistant specialized in answering questions about documents.
You have access to document sections that will be retrieved based on the user's question.
Follow these guidelines when responding:

1. Answer based ONLY on the context provided. If the context doesn't contain the answer, say "I don't have enough information to answer that question."
2. Be concise and direct, but provide complete answers.
3. If the retrieved context is highly relevant, begin with "Based on the document..."
4. For complex information, structure your answer with bullet points or numbered lists when appropriate.
5. When quoting directly from the document, use quotation marks.
6. If the user asks about something outside the document's scope, politely redirect them to topics covered in the documents.
7. Maintain a helpful, professional tone.

Remember: You are a document assistant, not a general AI, so focus solely on helping with the document content.

CONTEXT:
{context}

CHAT HISTORY:
{chat_history}

QUESTION:
{question}

YOUR ANSWER:"""

def get_llm(temperature=0.2, model="llama3:latest"):
    """Get the language model with improved parameters"""
    return Ollama(
        model=model,
        temperature=temperature,  # Lower for more factual responses
        repeat_penalty=1.1,       # Discourage repetition
        top_k=40,                 # Consider more token possibilities
        top_p=0.95,               # Sample from more probable tokens
        num_ctx=4096              # Larger context window for better understanding
    )

def get_conversation_chain(retriever, llm):
    """Create a conversation chain with enhanced prompt template and memory"""
    # Create an improved prompt template
    prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template=SYSTEM_TEMPLATE
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
    
    return conversation_chain

# Advanced feature: Contextual prompt enhancement based on document type
def get_domain_specific_prompt(document_type="general"):
    """Return domain-specific prompt templates based on document type"""
    prompts = {
        "legal": """You are a legal document analyst. Focus on precise interpretation of legal language.
                  Highlight important clauses, definitions, and potential implications.
                  Use legal terminology appropriately and explain complex terms when necessary.""",
        
        "technical": """You are a technical documentation specialist. Provide clear explanations of technical concepts.
                      When discussing procedures, present them as step-by-step instructions.
                      Emphasize key technical parameters and specifications.""",
        
        "academic": """You are an academic research assistant. Maintain scholarly tone and highlight methodology,
                     findings, and limitations. Reference relevant sections accurately and distinguish between
                     facts, hypotheses, and conclusions in the text.""",
        
        "general": SYSTEM_TEMPLATE
    }
    
    return prompts.get(document_type, SYSTEM_TEMPLATE)