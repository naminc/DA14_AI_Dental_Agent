# src/retriever/search.py
from rank_bm25 import BM25Okapi
import numpy as np
import json
import faiss
import re
from openai import OpenAI
from underthesea import word_tokenize
from src.config import *

class Retriever:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.index = faiss.read_index(str(FAISS_INDEX_PATH))

        with open(FAISS_METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
            
        # Chuẩn hóa corpus cho BM25
        corpus = [doc["content"] for doc in self.metadata]
        tokenized_corpus = [self.normalize_and_tokenize(text) for text in corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def normalize_text(self, text: str) -> str:
        text = text.lower()
        # Loại bỏ dấu câu nhưng giữ lại các ký tự đặc biệt y khoa nếu cần
        text = re.sub(r'[^\w\s]', ' ', text)
        text = " ".join(text.split())
        return text

    def normalize_and_tokenize(self, text: str):
        clean_text = self.normalize_text(text)
        # format="text" giúp kết nối các từ ghép như "sâu_răng", "niềng_răng"
        tokens = word_tokenize(clean_text, format="text").split()
        return tokens

    def embed_query(self, query):
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        return response.data[0].embedding

    def search(self, query, top_k=5):
        # 1. Vector Search (FAISS) - Lấy nhiều hơn top_k một chút để lọc
        query_vector = np.array([self.embed_query(query)], dtype="float32")
        distances, indices = self.index.search(query_vector, top_k * 3)
        
        # Lọc kết quả Vector có độ tương đồng cao (ngưỡng tùy chỉnh)
        vector_results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and dist < 0.5: # 0.5 là ngưỡng khoảng cách (càng nhỏ càng gần)
                vector_results.append(self.metadata[idx])

        # 2. Keyword Search (BM25)
        query_tokens = self.normalize_and_tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_idx = np.argsort(bm25_scores)[::-1][:top_k]
        bm25_results = [self.metadata[i] for i in bm25_idx if bm25_scores[i] > 0]

        # 3. Hybrid Merge (Ưu tiên Vector Search vì tính nghiêm túc và ngữ cảnh)
        unique_results = []
        seen_ids = set()

        # Đưa kết quả Vector vào trước
        for doc in vector_results:
            if doc["id"] not in seen_ids:
                unique_results.append(doc)
                seen_ids.add(doc["id"])

        # Sau đó bổ sung từ BM25 nếu chưa đủ top_k
        for doc in bm25_results:
            if doc["id"] not in seen_ids:
                unique_results.append(doc)
                seen_ids.add(doc["id"])
            if len(unique_results) >= top_k:
                break
            
        return unique_results[:top_k]