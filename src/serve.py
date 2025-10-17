# serve.py
from flask import Flask, request, jsonify
from pipeline import *

app = Flask(__name__)

# Initialize your pipeline once (so it's loaded in memory)
rag_pipeline = Pipeline(dataset_name="squad", query=["dummy question"])

@app.route("/invocations", methods=["POST"])
def invocations():
    data = request.get_json()
    questions = data.get("query", [])
    if not isinstance(questions, list):
        questions = [questions]

    # Run pipeline for each question
    results = []
    for q in questions:
        rag_pipeline.query = [q]
        rag_pipeline.run_pipeline()
        results.append({"question": q, "answer": rag_pipeline.answer})

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
