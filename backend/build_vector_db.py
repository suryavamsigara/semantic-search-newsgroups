import re
import tarfile
import pickle
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from transformers import logging
import faiss

logging.set_verbosity_error()

class SemanticSearch:
    def __init__(self, tar_path: str, model_name='all-MiniLM-L6-v2', max_docs: Optional[int] = None):
        self.tar_path = tar_path
        self.model = SentenceTransformer(model_name)
        self.max_docs = max_docs

        self.documents = [] # List of dict
        self.embeddings = None
        self.index = None

        # self._load_and_process()
        # self._create_index()
        # self.save("db")

    def clean_text(self, raw_bytes: bytes) -> str:
        try:
            text = raw_bytes.decode('utf-8', errors='ignore')

            # 1. Remove email headers
            if '\n\n' in text:
                text = text.split('\n\n', 1)[1]
            
            # 2. Split into lines for filtering
            lines = text.splitlines()
            cleaned = []

            # REGEX PATTERNS
            quote_pattern = re.compile(r'^[ \t]*([a-zA-Z0-9]{1,5}>|[-|}:]*>+|[>|}:]+)')
            # Catches ASCII borders, dividers, and underlines (e.g., ====, []---[], ****)
            divider_pattern = re.compile(r'^[ \t]*[-=_~+*\[\]]{3,}[ \t]*$')
            # Catches standard contact info (e.g., "Internet:", "Fax:", "Voice:")
            contact_pattern = re.compile(r'^[ \t]*(?:Internet|Voice|Fax|Phone|E-mail|Email|Tel)[ \t]*:', re.IGNORECASE)
            # Catches footer lead-ins (e.g., "For information on Toronto Siggraph... contact...")
            info_pattern = re.compile(r'^[ \t]*For (?:more |further )?information.*contact', re.IGNORECASE)

            for line in lines:
                stripped = line.strip()

                # Skip quotes
                if quote_pattern.match(stripped):
                    continue

                # Skip attributions (now case-insensitive and checks for pontificated)
                stripped_lower = stripped.lower()
                if stripped_lower.startswith('in article') or any(word in stripped_lower for word in ['writes:', 'says:', 'wrote:', 'pontificated:']):
                    continue
                
                # Skip ASCII dividers and header underlines (e.g., ====)
                if divider_pattern.match(stripped):
                    continue
                    
                # Skip contact info and boilerplate footer text
                if contact_pattern.match(stripped) or info_pattern.match(stripped):
                    continue
                
                # Skip very short fragments
                if len(stripped) < 5 and any(word in stripped.lower() for word in ['writes', 'article', 'says']):
                    continue

                cleaned.append(line)

            text = '\n'.join(cleaned)

            # 3. Signature and Footer Removal
            # Pattern A: Standard dashes (--)
            text = re.split(r'\n[ \t]*--+[ \t]*\n', text, maxsplit=1, flags=re.MULTILINE)[0]
            
            # Pattern B: Giant walls of asterisks, equals, or underscores (15+ characters)
            text = re.split(r'\n[ \t]*[-*=_~+|/\\\'.]{15,}', text, maxsplit=1)[0]
            
            # Pattern C: Common sign-offs (Best regards, Cheers, Sincerely) followed by a line break
            sign_off_pattern = r'\n[ \t]*(?:Best regards|Regards|Cheers|Sincerely|Thanks)[ \t]*,?[ \t]*\n'
            text = re.split(sign_off_pattern, text, maxsplit=1, flags=re.IGNORECASE)[0]

            # Pattern D: Long strings of periods (10+) used as inline dividers
            text = re.split(r'\.{10,}', text, maxsplit=1)[0]

            # 4. Handle any literal escaped quotes
            text = text.replace("\\'", "'").replace('\\"', '"')

            # 5. Fix newlines: turn single \n inside paragraphs into spaces
            text = re.sub(r'(?<=\S)\n(?=\S)', ' ', text)

            # 6. Clean extra whitespace
            text = re.sub(r' +', ' ', text)       
            text = re.sub(r'\n{3,}', '\n\n', text) 
            text = text.strip()

            # 7. Remove email signatures at the very end of the document
            text = re.sub(r'\n?\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\s*$', '', text, flags=re.MULTILINE)
        
            return text if text else "[Empty Document]"
        
        except Exception as e:
            print(f"Error processing document: {e}")
            return "[Processing Error]"
    
    def _load_and_process(self):
        """Load and process all documents from the tar file"""
        print("Loading 20 Newsgroups dataset...")

        with tarfile.open(self.tar_path, "r:gz") as tar:
            members = tar.getmembers()

            file_members = [m for m in members if m.isfile() and len(m.name.split('/')) >= 3]

            if self.max_docs:
                file_members = file_members[:self.max_docs]

            print(f"Processing {len(file_members)} documents...")

            for member in tqdm(file_members, desc="Processing documents"):
                path_parts = member.name.split('/')
                if len(path_parts) >= 3:
                    category = path_parts[-2] # sci.space, comp.graphics,...
                    filename = path_parts[-1]

                    f = tar.extractfile(member)
                    if f is not None:
                        raw_bytes = f.read()
                        cleaned_text = self.clean_text(raw_bytes)

                        # Store document
                        self.documents.append({
                            'text': cleaned_text,
                            'category': category,
                            'filename': filename,
                            'full_path': member.name
                        })
        print(f"Loaded {len(self.documents)} documents.")
    
    def _create_index(self):
        """Create Faiss index from document embeddings"""
        print("\nGenerating embeddings...")

        texts = [doc['text'] for doc in self.documents]
        embedding_list = []

        batch_size = 64
        for i in tqdm(range(0, len(texts), batch_size), desc="Creating embeddings"):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embedding_list.append(batch_embeddings)
        
        # Combine all embeddings
        self.embeddings = np.vstack(embedding_list).astype('float32')

        # Normalize for cosine similarity
        faiss.normalize_L2(self.embeddings)

        # Create FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(self.embeddings)

        print(f"✅ FAISS index created with {self.index.ntotal} vectors")
        print(f"Embedding dimension: {dimension}")

    def save(self, path: str):
        """Save index and metadata"""
        faiss.write_index(self.index, f"{path}/index.faiss")

        with open(f"{path}/metadata.pkl", "wb") as f:
            pickle.dump({
                'num_documents': len(self.documents),
                'model_name': 'all-MiniLM-L6-v2'
            }, f)

        with open(f"{path}/documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)
        
        print(f"✅ Saved to {path}")

    def load(self, path: str):
        self.index = faiss.read_index(f"{path}/index.faiss")

        with open(f"{path}/metadata.pkl", "rb") as f:
            metadata = pickle.load(f)
            print(f"Loaded index built with: {metadata['model_name']}")
        
        with open(f"{path}/documents.pkl", "rb") as f:
            self.documents = pickle.load(f)
        
        print(f"✅ Successfully loaded {len(self.documents)} documents from {path}")

    def search(self, query: str, k: int = 5):
        query_embedding = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, min(k, len(self.documents)))

        results = []

        for score, idx in zip(scores[0], indices[0]):
            doc = self.documents[idx]

            results.append({
                'rank': len(results) + 1,
                'score': float(score),
                'text': doc['text'],
                'category': doc['category'],
                'filename': doc['filename']
            })

            if len(results) >= k:
                break
        
        return results


if __name__ == "__main__":
    TAR_FILE_PATH = "20_newsgroups.tar.gz"
    search = SemanticSearch(tar_path=TAR_FILE_PATH, model_name='BAAI/bge-small-en-v1.5')
    
    # print(search.search("Not that religion warrants belief, but the belief carries with it some psychological benefits."))