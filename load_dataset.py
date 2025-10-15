import logging
from datasets import load_dataset
from tqdm import tqdm

import os; os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY','YES')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadDataset:
	def __init__(self, dataset_name, split='train', max_documents=500):
		self.dataset_name = dataset_name
		self.split = split
		self.max_documents = max_documents
		
		self.documents = []
	
	def load_text_corpus(self):
		logger.info(f"Loading dataset {self.dataset_name} split={self.split}")
		
		ds = load_dataset(self.dataset_name, split=self.split)
		
		for i, ex in enumerate(tqdm(ds)):
			if i >= self.max_documents:
				break
			
			# Heuristics for common fields
			text = None
			meta = {}
			
			for key in ['context', 'article', 'text', 'passage', 'content', 'paragraph']:
				if key in ex and ex[key]:
					text = ex[key]
					break
					
			if text is None:
				# fallback: join stringifiable values
				text = ' '.join([str(v) for v in ex.values() if isinstance(v, str)])
				
			if not text:
				continue
				
			self.documents.append({'id': f"doc_{i}", 'text': text, 'meta': {}})
			
		logger.info(f"Loaded {len(self.documents)} documents")
