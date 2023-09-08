import os
from langchain.embeddings import HuggingFaceEmbeddings 
from langchain.vectorstores import Chroma 
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask import Flask, render_template
from pipeline import initalize_dataPipe
from chroma import addPDFToDatabase
from logger import LoggerWrapper, FeedbackType, Mode as LoggerMode
from argparse import ArgumentParser
from werkzeug.utils import secure_filename
import requests
import time
import base64
import json

load_dotenv()
db_folder_name = os.getenv('DB_FOLDER_NAME')
pdf_folder_name = os.getenv('PDF_FOLDER_NAME')
proxy_url = os.getenv("OPENAI_PROXY")
api_key = os.getenv("OPENAI_API_KEY")
embeddings = HuggingFaceEmbeddings(model_name=os.getenv("HUGGINGFACE_MODEL"))

# version des prompts bzw der Antwortgennerierung um im log die Qualität der Antwortgennerierung in Logs zu verfolgen
# BITTE ANPASSEN, WENN DER PROMPT GEÄNDERT WIRD !!!
prompt_version = "try_1_roleprompting"

#setup gpt
temperature = 1.0

#init server
app = Flask(__name__)

@app.route('/')
def home():
   return render_template('home.html')


@app.route('/chat', methods=['GET'])
def chat_page():
    return render_template('chat.html')

# sende einen post request mit json bspl: {"query": "ich würde gerne etwas wissen zu Variablen"}
@app.route('/query', methods=['POST'])
def process_query():
    start_time = int(round(time.time() * 1000))
    global temperature
    query = request.json['query']
    # lade vectordatenbank und mache simsearch für die zusatzinformationen
    vectordb = Chroma(persist_directory=db_folder_name, embedding_function=embeddings)
    docs = vectordb.similarity_search(query)

    additional_content = ''

    for i in range(min(len(docs),10)):
        additional_content += docs[i].page_content + '\n\n'
    
    # Bereite den JSON-Payload für den GPT Proxy vor   
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "You are a computer science teacher very well versed in your subject." +
                "Answer this question exactly and only, in maximum 5 sentences:\n\n" 
                + ' ' + query + "\n\n" +
                "Answere in english! To answer this question, you have acquired the following additional knowledge and background, " +
                "use it in your answer if possible:\n\n" 
                + ' ' + additional_content + ""
            }
        ],
        "temperature": temperature
    }
    try:
        # im Testmodus wird kein Request an den Proxy gesendet
        if test_mode is False:
            # Sende POST-Request an den Proxy-Server
            response = requests.post(proxy_url, headers={'Authorization': api_key}, json=payload)
            response_json = response.json()
        else:
            # Lade Fakeantwort aus Datei
            with open('test_response.json', 'r') as f:
                response_json = json.load(f)

        # Extrahiere die Antwort
        response_gpt =  response_json['choices'][0]['message']['content']
        response_gpt = response_gpt.split('\n')

        # logging
        logger.log_tokens(prompt_version,123, response_json['usage']['prompt_tokens'], response_json['usage']['completion_tokens'])
        logger.log_complete_response(prompt_version=prompt_version,id = 123, tokens_input= response_json['usage']['prompt_tokens'],tokens_output= response_json['usage']['completion_tokens'], 
                                     start_time=start_time,end_time=round(time.time() * 1000),
                                     question=payload['messages'][0]['content'], answer=response_json['choices'][0]['message']['content'])

    except:
        print('Error: Request to GPT-3 failed')

    logger.log_speed(prompt_version, 123, start_time, round(time.time() * 1000))

    return jsonify(response_gpt)

# feedback
@app.route('/feedback', methods=['POST'])
def receive_feedback():
    global temperature
    feedback = request.json['feedback']

    if feedback == 'increment':
        temperature += 0.1  
    elif feedback == 'decrement':
        temperature -= 0.1  

    logger.log_feedback(prompt_version, 123, feedback, FeedbackType.RELEVANCE)

    response = {
        'status': 'success',
        'message': 'Feedback erfolgreich empfangen',
        'temperature': temperature
    }
    return jsonify(response), 200

#show pdf titles
@app.route('/get_pdf_titles')
def get_pdf_titles():
    pdf_folder = 'lecture_slides_pdfs'  # Update this with your folder path
    pdf_titles = [pdf.split('.')[0] for pdf in os.listdir(pdf_folder) if pdf.endswith('.pdf')]
    return jsonify(pdf_titles)

#upload of pdf
@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'pdf_data' not in request.json or 'pdf_title' not in request.json:
        return 'Error: PDF data or title is missing', 400
    
    pdf_data = request.json['pdf_data']
    pdf_title = request.json['pdf_title']  # Get the PDF title
    
    # Construct the filename with the provided title
    filename = f"{pdf_title}.pdf"
    savePath = f"{pdf_folder_name}{filename}"
    decoded_pdf_data = base64.b64decode(pdf_data)

    with open(savePath, 'wb') as file:
        file.write(decoded_pdf_data)
    
    vectordb = Chroma(persist_directory=db_folder_name, embedding_function=embeddings)
    addPDFToDatabase(vectordb, filename)

    return 'PDF file successfully received and added to the database', 200


if __name__ == "__main__":
    
    parser = ArgumentParser()
    parser.add_argument("-t", "--test", action = 'store_true',required=False, help='Enable to test without using the API')
    parser.add_argument("-l", "--logging_mode", type=LoggerMode, choices=LoggerMode, default=LoggerMode.FULL,required=False,
                        help='Select a mode for logging from: NONE, FULL, ALLINONE, ALLSEPARATE')
    args = parser.parse_args()
    
    # Enable to test without using the API and using the budget
    global test_mode
    test_mode = args.test
    # Logger initilaization
    global logger 
    logger = LoggerWrapper(args.logging_mode)

    years = ['2022']
    months = ['01', '02', '03', '04', '05', '06','07', '08', '09', '10', '11', '12']
    ## use lda or gpt for getting topics of pdfs
    initalize_dataPipe(topics='lda', years=years, months=months)

    #starte server
    app.run(host='0.0.0.0', port=5000)
