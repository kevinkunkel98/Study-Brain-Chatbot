from dotenv import load_dotenv
import os
import pandas as pd
from pdfminer.high_level import extract_text
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from gensim import corpora, models
import requests

def preprocess_text(text):
    tokens = word_tokenize(text)
    tokens = [token.lower() for token in tokens if token.isalnum()]
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return tokens

def extract_topics_from_pdfs_lda(directory):
    files = os.listdir(directory)
    topics = []
    
    for file in files:
        if file.endswith('.pdf'):
            file_path = os.path.join(directory, file)
            
            # Extrahiere Text aus dem PDF
            text = extract_text(file_path)
            # preprocessing
            tokens = preprocess_text(text)

            topics.append({'dir': file_path, 'topics': tokens})
    
    # Erstelle Dictionary und Corpus
    texts = [topic['topics'] for topic in topics]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    
    # Führe LDA-Modellierung durch
    lda_model = models.LdaModel(corpus, num_topics=5, id2word=dictionary)
    
    # Extrahiere Hauptthemen für jedes Dokument
    extracted_topics = lda_model.get_document_topics(corpus)
    topics_list = [[topic[0] for topic in extracted_topic] for extracted_topic in extracted_topics]
    
    # Aktualisiere DataFrame mit extrahierten Themen
    for i, topic_list in enumerate(topics_list):
        topic_terms = []
        for topic_id in topic_list:
            topic_terms.append(lda_model.show_topic(topic_id, topn=5))
        topic_words = [[term[0] for term in terms] for terms in topic_terms]
        unique_words = list(set([word for sublist in topic_words for word in sublist]))
        topics[i]['topics'] = unique_words    
    
    # Erstelle Pandas DataFrame
    df = pd.DataFrame(topics)
    return df

def extract_topics_from_pdfs_gpt(directory, proxy_url, api_key):
    files = os.listdir(directory)
    topics = []
    
    for file in files:
        if file.endswith('.pdf'):
            file_path = os.path.join(directory, file)
            
            # Extrahiere Text aus dem PDF
            text = extract_text(file_path)
            
            # Preprocessing des Textes
            tokens = preprocess_text(text)

            # Bereite den JSON-Payload vor
            payload = {
                "messages": [
                    {
                      "role": "user",
                      "content": "Extract 5 topics from the following text. Only 1 word for the topic:\n\n" + ' '.join(tokens) + "\n\nTopics:"
                    }
                ],
            }

            try:
               # Sende POST-Request an den Proxy-Server
               response = requests.post(proxy_url, headers={'Authorization': api_key}, json=payload)
               response_json = response.json()
               # Extrahiere die Themen aus der Antwort
               response_topics =  response_json['choices'][0]['message']['content']
               response_topics = response_topics.split('\n')
               topics_text = [topic.split('. ')[1] for topic in response_topics if topic]
               topics_text = [topic for topic in topics_text if topic]  # Entferne leere Strings
               topics.append({'dir': file, 'topics': topics_text})
            except:
                print('err')
    
    # Erstelle Pandas DataFrame
    df = pd.DataFrame(topics)
    return df

if __name__ == "__main__":
    load_dotenv()
    pdf_folder_path = os.getenv("PDF_FOLDER_NAME")
    proxy_url = os.getenv("OPENAI_PROXY")
    api_key = os.getenv("OPENAI_API_KEY")

    df_lda = extract_topics_from_pdfs_lda(pdf_folder_path)
    print(df_lda.head(5))
    flat_list = [word for sublist in df_lda['topics'] for word in sublist]
    print('Topics der pdfs: ' + str(list(set(flat_list))))

    #df_gpt = extract_topics_from_pdfs_gpt(pdf_folder_path, proxy_url, api_key)
    #print(df_gpt.head(5))
