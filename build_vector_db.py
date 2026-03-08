import os
import re
import json
import tarfile
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def clean_text(raw_bytes):
    """
    The dataset is noisy. We discard routing headers,
    quoted replies, emails, URLs, and signatures to ensure the embeddings 
    only capture the core semantic content.
    """
    try:
        text = raw_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return ""
    
    # Split header from body
    parts = text.split('\n\n', 1)
    if len(parts) > 1:
        text = parts[1]
        
    lines = text.split('\n')
    # Remove quoted text from previous replies
    lines = [line for line in lines if not line.strip().startswith('>')]
    text = '\n'.join(lines)
    
    # Remove emails and URLs
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'http\S+', '', text)
    
    # Remove signatures (commonly separated by -- or __)
    text = re.split(r'\n--\s*\n|\n__+\n', text)[0]
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def setup_vector_database(tar_path, emb_out_dir, max_docs=None):
    os.makedirs(emb_out_dir, exist_ok=True)
    
    documents = []
    metadata = []
    
    print(f"Reading and cleaning files from {tar_path}...")
    # Open the dataset
    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tqdm(tar.getmembers(), desc="Processing Archive"):
            # if len(documents) >= max_docs:
            #     break
                
            if member.isfile():
                # Extract category and filename
                path_parts = member.name.split('/')
                if len(path_parts) >= 3:
                    category = path_parts[-2]
                    doc_id = path_parts[-1]
                    
                    f = tar.extractfile(member)
                    if f is not None:
                        raw_bytes = f.read()
                        cleaned_text = clean_text(raw_bytes)
                        
                        # Discard short documents as they lack semantic value 
                        if len(cleaned_text) > 50:
                            documents.append(cleaned_text)
                            metadata.append({
                                "doc_id": doc_id,
                                "category": category,
                                "text": cleaned_text
                            })

    print(f"Retained {len(documents)} clean documents.")

    print("Loading embedding model and encoding texts...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    all_embeddings = model.encode(documents, show_progress_bar=True, batch_size=64)
    
    # Save the embeddings and metadata
    all_embeddings = np.array(all_embeddings)
    emb_path = os.path.join(emb_out_dir, "newsgroup_embeddings.npy")
    meta_path = os.path.join(emb_out_dir, "metadata.jsonl")
    
    print(f"Saving embeddings to: {emb_path}")
    np.save(emb_path, all_embeddings)
    
    print(f"Saving metadata to: {meta_path}")
    with open(meta_path, 'w', encoding='utf-8') as f:
        for meta in metadata:
            f.write(json.dumps(meta) + '\n')
            
    print("Database setup complete.")
    return emb_path, meta_path

if __name__ == "__main__":
    TAR_FILE_PATH = "20_newsgroups.tar.gz"
    OUTPUT_DIRECTORY = "./vector_db"
    
    setup_vector_database(TAR_FILE_PATH, OUTPUT_DIRECTORY)
