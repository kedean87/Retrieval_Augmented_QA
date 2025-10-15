import logging
import numpy as np
from nltk.tokenize import sent_tokenize
from sklearn.preprocessing import normalize

import os; os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY','YES')
import faiss, torch; torch.set_num_threads(1);

# sentence transformers for embeddings
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import faiss
    _HAS_FAISS = True
except Exception:
    _HAS_FAISS = False

class Database:
	def __init__(self, documents, model_name='sentence-transformers/all-MiniLM-L6-v2', max_tokens=200, overlap=50, batch_size=32):
		self.documents = documents
		self.model_name = model_name
		self.batch_size = batch_size
		
		self.max_tokens = max_tokens
		self.overlap = overlap
		
		self.chunks = None
		self.embeddings = None
		self.index = None
		self.ids = None
		self.embed_model = None
		self.pooled = None
		
	def chunks_from_text(self, text):
		"""Simple heuristic chunking: split text into sentences then accumulate until max_tokens (approx by words).
		Overlap in words between chunks.
		"""
		sents = sent_tokenize(text)
		chunks = []
		cur_chunk = []
		cur_len = 0
		
		for sent in sents:
			words = sent.split()
			
			if cur_len + len(words) > self.max_tokens and cur_chunk:
				chunks.append(' '.join(cur_chunk))
				
				# start new chunk with overlap
				if self.overlap > 0:
					overlap_words = max(1, self.overlap)
					cur_chunk = cur_chunk[-overlap_words:]
					cur_len = len(cur_chunk)
				else:
					cur_chunk = []
					cur_len = 0
			
			cur_chunk.append(sent)
			cur_len += len(words)
			
		if cur_chunk:
			chunks.append(' '.join(cur_chunk))
			
		return chunks

	def build_chunks(self):
		"""Return list of chunks: {'id', 'doc_id', 'text', 'meta'}"""
		chunks = []
		for d in self.documents:
			doc_id = d['id']
			text = d['text']
			c = self.chunks_from_text(text)
			print(c)
			
			for i, chunk in enumerate(c):
				chunks.append({'id': f"{doc_id}_chunk_{i}", 'doc_id': doc_id, 'text': chunk, 'meta': d.get('meta', {})})
		
		logger.info(f"Built {len(chunks)} chunks from {len(self.documents)} documents")
		
		self.chunks = chunks

	def build_embeddings(self):
		"""Return embeddings matrix (N x D) and list of ids.
		"""
		logger.info(f"Loading embedding model: {self.model_name}")
		self.embed_model = SentenceTransformer(self.model_name)
		
		texts = [c['text'] for c in self.chunks]
		
		embeddings = self.embed_model.encode(texts, batch_size=self.batch_size, show_progress_bar=True)
		
		# normalize
		self.embeddings = normalize(embeddings)
		self.ids = [c['id'] for c in self.chunks]

	def build_faiss_index(self, index_path):
		if not _HAS_FAISS:
			logger.warning("FAISS not installed. Install faiss-cpu or faiss-gpu to use FAISS.")
			return None
		
		d = self.embeddings.shape[1]
		
		# Using IndexFlatIP for cosine similarity (after normalization)
		self.index = faiss.IndexFlatIP(d)
		
		logger.info("Adding embeddings to FAISS index")
		
		self.index.add(self.embeddings.astype('float32'))

		# Optionally save
		if index_path:
			faiss.write_index(self.index, index_path)

	def faiss_query(self, query_emb, k=5):
		if self.index is None:
			return []
			
		if query_emb.ndim == 1:
			query_emb = query_emb.reshape(1, -1)
			
		D, I = self.index.search(query_emb.astype('float32'), k)
		
		return I[0], D[0]
	
	
