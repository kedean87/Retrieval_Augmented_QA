from pipeline import *

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
	demo_questions = [
		"What is the main idea of the passage?",
		"Who was mentioned in the passage?",
		"When did the event occur?",
		]

	rag_pipeline = Pipeline(
		dataset_name='squad',
		query=demo_questions,
		)

	rag_pipeline.run_pipeline()

if __name__ == "__main__":
	main()
