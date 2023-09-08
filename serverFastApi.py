import os
from langchain.embeddings import HuggingFaceEmbeddings 
from langchain.vectorstores import Chroma 
from dotenv import load_dotenv
from pipeline import initalize_dataPipe
from chroma import addPDFToDatabase
import requests
import time
import base64
from fastapi import FastAPI, Request, HTTPException
import uvicorn

load_dotenv()
db_folder_name = os.getenv('DB_FOLDER_NAME')
pdf_folder_name = os.getenv('PDF_FOLDER_NAME')
proxy_url = os.getenv("OPENAI_PROXY")
api_key = os.getenv("OPENAI_API_KEY")
embeddings = HuggingFaceEmbeddings(model_name=os.getenv("HUGGINGFACE_MODEL"))

#setup gpt
temperature = 1.0

#init server
app = FastAPI()

# sende einen post request mit json bspl: {"query": "ich würde gerne etwas wissen zu Variablen"}
@app.post('/query')
async def process_query(request: Request):
    global temperature
    data = await request.json() 
    query = data['query']
    # lade vectordatenbank und mache simsearch für die zusatzinformationen
    vectordb = Chroma(persist_directory=db_folder_name, embedding_function=embeddings)
    docs = vectordb.similarity_search(query)
    additional_content = docs[0].page_content

    # Bereite den JSON-Payload für den GPT Proxy vor   
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Kannst du mir folgende Frage beantworten:\n\n" + ' '.join(query) + 
                "\n\n. Hier ist etwas Zusatzinformation und Hintergrundwissen zu der Frage: " + ' '.join(additional_content)
            }
        ],
        "temperature": temperature
    }

    try:
        # Sende POST-Request an den Proxy-Server
        response = requests.post(proxy_url, headers={'Authorization': api_key}, json=payload)
        response_json = response.json()
        # Extrahiere die Antwort
        response_gpt =  response_json['choices'][0]['message']['content']
        response_gpt = response_gpt.split('\n')
    except:
        print('err')

    return { "message": response_gpt }

# feedback
@app.post('/feedback')
async def receive_feedback(request: Request):
    global temperature
    data = await request.json()
    feedback = data['feedback']

    if feedback == 'increment':
        temperature += 0.1  
    elif feedback == 'decrement':
        temperature -= 0.1  

    response = {
        'status': 'success',
        'message': 'Feedback erfolgreich empfangen',
        'temperature': temperature
    }
    return response
    

#upload einer neuen pdf in einer base64 kodierten form
@app.post('/upload-pdf')
async def upload_pdf(request: Request):
    # Überprüfe, ob ein JSON-Payload mit 'pdf_data' im Request-Body vorhanden ist
    data = await request.json()
    if 'pdf_data' not in data:
        raise HTTPException(status_code=400, detail='Error: PDF data is missing')
    
    pdf_data = data['pdf_data']
    
    # Speichere als PDF-Datei
    timestamp = str(int(time.time()))
    filename = f"{timestamp}.pdf"
    savePath = f"{pdf_folder_name}/addPdf/{timestamp}.pdf"
    decoded_pdf_data = base64.b64decode(pdf_data)


    with open(savePath, 'wb') as file:
        file.write(decoded_pdf_data)
    
    vectordb = Chroma(persist_directory=db_folder_name, embedding_function=embeddings)
    addPDFToDatabase(vectordb, filename )

    return 'PDF-Datei erfolgreich empfangen und der Datenbank hinzugefügt'

if __name__ == "__main__":
    years = ['2020', '2021', '2022', '2023']
    months = ['01', '02', '03', '04', '05', '06','07', '08', '09', '10', '11', '12']
    #initalize_dataPipe(topics='lda', years=["2023"], months=["06"])

    #starte server
    uvicorn.run("serverFastApi:app", host="0.0.0.0", port=8000)
