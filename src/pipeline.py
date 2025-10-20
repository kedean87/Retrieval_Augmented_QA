import logging
import numpy as np

from sklearn.preprocessing import normalize
from model import *
from vector_database import *
from load_dataset import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import faiss
    _HAS_FAISS = True
except Exception:
    _HAS_FAISS = False

class Pipeline:
	def __init__(self, dataset_name, query, model=None, tokenizer=None, top_k=4, max_length=256):
		self.dataset_name = dataset_name
		self.model = model
		self.tokenizer = tokenizer
		self.query = query
		self.top_k = top_k
		self.max_length = max_length
		
		self.retrieved_texts = None
		self.question = None
		self.answer = None
		self.answers = None
		self.dbase = None
		self.id2chunk = None
	
	def generate_answer_with_model(self, prompt=""):
		for i, t in enumerate(self.retrieved_texts):
			prompt += f"[Passage {i+1}] {t}\n\n"
			
		prompt += f"Question: {self.question}\nAnswer:" 
		
		inputs = self.tokenizer(prompt, return_tensors='pt', truncation=True, max_length=1024)
		out = self.model.generate(**inputs, max_length=self.max_length, num_beams=4, early_stopping=True)
		
		self.answer = self.tokenizer.decode(out[0], skip_special_tokens=True)
	
	def build_database(self):
		rm = RAGModel()
		self.tokenizer = rm.tokenizer
		self.model = rm.model
		
		ld = LoadDataset(
			dataset_name=self.dataset_name, 
			split='train', 
			max_documents=500)
		ld.load_text_corpus()
		
		dbase = Database(
			documents=ld.documents, 
			model_name='sentence-transformers/all-MiniLM-L6-v2', 
			max_tokens=200, 
			overlap=50, 
			batch_size=32
			)
		dbase.build_chunks()
		dbase.build_embeddings()
		
		self.dbase = dbase
		
		faiss_index = None
		if _HAS_FAISS:
			dbase.build_faiss_index(index_path=None)
		else:
			logger.warning("FAISS unavailable; will use brute-force search for demo")
		
		# Create mapping id -> chunk text
		id2chunk = {c['id']: c['text'] for c in dbase.chunks}
		self.id2chunk = id2chunk
	
	def retrieve_documents_and_answer(self):
		self.answers = []
		demo_questions = self.query
		
		for q in demo_questions:
			self.question = q
			logger.info(f"Running demo query: {self.question}")
			
			q_emb = self.dbase.embed_model.encode([q])
			q_emb = normalize(q_emb)
			
			self.retrieved_texts = []
			
			if self.dbase.index is not None:
				I, D = self.dbase.faiss_query(q_emb, k=self.top_k)
				
				for idx in I:
					try:
						cid = ids[int(idx)]
						self.retrieved_texts.append(self.id2chunk[cid])
					except Exception:
						pass
			else:
				# brute force
				sims = np.dot(self.dbase.embeddings, q_emb.T).squeeze()
				top_idx = np.argsort(-sims)[:self.top_k]
				
				for ti in top_idx:
					self.retrieved_texts.append(self.id2chunk[dbase.ids[ti]])
			
			# Generate answer
			self.generate_answer_with_model()
			
			print("\n--- QUERY ---\n", self.question, "\n--- TOP retrieved passages ---\n")
			
			for i, t in enumerate(self.retrieved_texts):
				print(f"[{i+1}]", t[:400].replace('\n', ' '), '...')
				
			print("\n--- GENERATED ANSWER ---\n", self.answer, "\n===============================\n")
			self.answers.append( self.answer )

	def run_pipeline(self):
		rm = RAGModel()
		self.tokenizer = rm.tokenizer
		self.model = rm.model
		
		ld = LoadDataset(
			dataset_name=self.dataset_name, 
			split='train', 
			max_documents=500)
		ld.load_text_corpus()
		
		dbase = Database(
			documents=ld.documents, 
			model_name='sentence-transformers/all-MiniLM-L6-v2', 
			max_tokens=200, 
			overlap=50, 
			batch_size=32
			)
		dbase.build_chunks()
		dbase.build_embeddings()
		
		if _HAS_FAISS:
			dbase.build_faiss_index(index_path=None)
		else:
			logger.warning("FAISS unavailable; will use brute-force search for demo")
		
		# Create mapping id -> chunk text
		id2chunk = {c['id']: c['text'] for c in dbase.chunks}

		demo_questions = self.query
		
		for q in demo_questions:
			self.question = q
			logger.info(f"Running demo query: {self.question}")
			
			q_emb = dbase.embed_model.encode([q])
			q_emb = normalize(q_emb)
			
			self.retrieved_texts = []
			
			if dbase.index is not None:
				I, D = dbase.faiss_query(q_emb, k=self.top_k)
				
				for idx in I:
					try:
						cid = ids[int(idx)]
						self.retrieved_texts.append(id2chunk[cid])
					except Exception:
						pass
			else:
				# brute force
				sims = np.dot(dbase.embeddings, q_emb.T).squeeze()
				top_idx = np.argsort(-sims)[:self.top_k]
				
				for ti in top_idx:
					self.retrieved_texts.append(id2chunk[dbase.ids[ti]])
			
			# Generate answer
			self.generate_answer_with_model()
			
			print("\n--- QUERY ---\n", self.question, "\n--- TOP retrieved passages ---\n")
			
			for i, t in enumerate(self.retrieved_texts):
				print(f"[{i+1}]", t[:400].replace('\n', ' '), '...')
				
			print("\n--- GENERATED ANSWER ---\n", self.answer, "\n===============================\n")
			
		
		
		








