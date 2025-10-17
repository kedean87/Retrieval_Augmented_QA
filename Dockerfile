FROM python:3.10-slim

WORKDIR /app
COPY src/ /app

# Step 1: Install CPU-only torch first
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Step 2: Install the rest of your dependencies (will reuse that torch)
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask

RUN python -m nltk.downloader punkt punkt_tab averaged_perceptron_tagger wordnet

EXPOSE 8080
ENTRYPOINT ["python", "serve.py"]
CMD ["serve"]

