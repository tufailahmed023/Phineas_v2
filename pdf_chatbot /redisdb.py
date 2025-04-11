import redis
import numpy as np
import json

# Cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
 
# Store embedding & response in Redis
def store_in_cache(query, response, embedding):
    key = f"q:{query}"
    redis_client.set(key, json.dumps({
        'response': response,
        'embedding': embedding.tolist()
    }))

# Try to retrieve semantically similar answer
def get_similar_from_cache(query_embedding, threshold=0.90):
    redis_client = redis.Redis(host='localhost', port=6383, db=0)
    for key in redis_client.scan_iter(match="q:*"):
        data = json.loads(redis_client.get(key))
        cached_embedding = np.array(data['embedding'])
        score = cosine_similarity(query_embedding, cached_embedding)
        if score >= threshold:
            return data['response']
    return None

 
