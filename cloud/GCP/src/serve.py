from flask import Flask, request, jsonify
from pipeline import *

app = Flask(__name__)

# Initialize your pipeline once (so it's loaded in memory)
rag_pipeline = Pipeline(dataset_name="squad", query=["dummy question"])
rag_pipeline.run_pipeline()  # optional warm-up

# Get the health and prediction routes from Vertex AI environment variables
health_route = os.environ.get('AIP_HEALTH_ROUTE', '/')
predict_route = os.environ.get('AIP_PREDICT_ROUTE', '/predict')

# Health check for any GET request
@app.route(health_route, methods=["GET"])
def health():
    return "Healthy", 200

# Prediction endpoint
@app.route(predict_route, methods=["POST"])
def predict():
    data = request.get_json()
    questions = data.get("instances", [])
    if not isinstance(questions, list):
        questions = [questions]

    results = []
    for q in questions:
        query = q.get("query") if isinstance(q, dict) else q
        rag_pipeline.query = [query]
        rag_pipeline.run_pipeline()
        results.append({"question": query, "answer": rag_pipeline.answer})

    response = {
        "predictions": [
            {
                "results": results
            }
        ]
    }
        
    final_json = json.dumps(response)
    print(f"Final response body: {final_json}")
    
    return jsonify(final_json)

if __name__ == "__main__":
    # IMPORTANT: Use port 8080 for Vertex AI.
    app.run(host="0.0.0.0", port=int(os.environ.get('AIP_HTTP_PORT', 8080)))
