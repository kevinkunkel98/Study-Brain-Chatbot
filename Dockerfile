# Image for the Chatbot application
FROM python:3.9
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN python -c 'import nltk; nltk.download("punkt"); nltk.download("stopwords"); nltk.download("wordnet")'
#RUN python scrapeMedium.py
EXPOSE 5000
CMD ["python", "server.py"]
