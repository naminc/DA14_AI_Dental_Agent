# import json
# from pathlib import Path

# import faiss
# import numpy as np
# from openai import OpenAI

# from src.config import (
#     RAW_DATA_PATH,
#     PROCESSED_DATA_PATH,
#     FAISS_INDEX_PATH,
#     FAISS_METADATA_PATH,
#     OPENAI_API_KEY,
#     EMBEDDING_MODEL,
# )


# def load_dataset():
#     with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
#         return json.load(f)


# def save_processed_chunks(data):
#     PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
#     with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)


# def get_embedding(client: OpenAI, text: str):
#     response = client.embeddings.create(
#         model=EMBEDDING_MODEL,
#         input=text
#     )
#     return response.data[0].embedding


# def build_faiss_index():
#     if not OPENAI_API_KEY:
#         raise ValueError("Thiếu OPENAI_API_KEY trong file .env")

#     client = OpenAI(api_key=OPENAI_API_KEY)
#     data = load_dataset()

#     texts = []
#     metadata = []
#     embeddings = []

#     for item in data:
#         text = item["content"].strip()
#         emb = get_embedding(client, text)

#         texts.append(text)
#         metadata.append(item)
#         embeddings.append(emb)

#     vectors = np.array(embeddings, dtype="float32")
#     dimension = vectors.shape[1]

#     index = faiss.IndexFlatL2(dimension)
#     index.add(vectors)

#     FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
#     faiss.write_index(index, str(FAISS_INDEX_PATH))

#     with open(FAISS_METADATA_PATH, "w", encoding="utf-8") as f:
#         json.dump(metadata, f, ensure_ascii=False, indent=2)

#     save_processed_chunks(metadata)

#     print(f"Đã lưu index: {FAISS_INDEX_PATH}")
#     print(f"Đã lưu metadata: {FAISS_METADATA_PATH}")
#     print(f"Tổng số chunks: {len(metadata)}")


# if __name__ == "__main__":
#     build_faiss_index()