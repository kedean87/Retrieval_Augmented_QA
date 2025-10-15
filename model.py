import os; os.environ.setdefault('OBJC_DISABLE_INITIALIZE_FORK_SAFETY','YES')
import faiss, torch; torch.set_num_threads(1);

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGModel:
	def __init__(self, model_name='google/flan-t5-small'):
		self.tokenizer = AutoTokenizer.from_pretrained(model_name)
		self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
