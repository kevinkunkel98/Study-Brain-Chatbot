from dotenv import load_dotenv
import os
from langchain.document_loaders import PyPDFDirectoryLoader, PyPDFLoader
from langchain.vectorstores import Chroma 
from langchain.embeddings import HuggingFaceEmbeddings 
from langchain.document_loaders import TextLoader
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import WikipediaLoader

# Setup
load_dotenv()
os.environ["OPENAI_PROXY"] = os.getenv("OPENAI_PROXY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
db_folder_name = os.getenv('DB_FOLDER_NAME')
pdfFolderPath = os.getenv("PDF_FOLDER_NAME")
additionalTxtFolderName = os.getenv('SCRAPE_FOLDER_NAME')

#embeddings
embeddings = HuggingFaceEmbeddings(model_name=os.getenv("HUGGINGFACE_MODEL"))

def createDatabase(pdfFolderPath, embeddings, db_folder_name):
    #load pdfs
    loader = PyPDFDirectoryLoader(pdfFolderPath)
    docs = loader.load()
    #create embeddings and vectors
    vectordb = Chroma.from_documents(docs, embedding=embeddings, persist_directory=db_folder_name)
    vectordb.persist()

#adds single pdfs to db
def addPDFToDatabase(vectordb, fileName):
   loader = PyPDFLoader(pdfFolderPath + fileName)
   pages = loader.load_and_split()
   vectordb.add_documents(pages)
   vectordb.persist()

def addTxtFromFolder(vectordb, additionalTxtFolderName, ):
    loader = DirectoryLoader(additionalTxtFolderName, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()
    # Split documents into small chunks. This is so we can find the most relevant chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents) 
    vectordb.add_documents(texts)
    vectordb.persist()

def addWikiInfos(vectordb, query):
    docs = WikipediaLoader(query=query, load_max_docs=2).load()
    vectordb.add_documents(docs)
    vectordb.persist()

if __name__ == "__main__":
    if not os.path.exists(db_folder_name):
        createDatabase()
    
    #load existing chromadb
    vectordb = Chroma(persist_directory=db_folder_name, embedding_function=embeddings)

    # addPDFToDatabase(vectordb, + 'addPdf/Gitlab-Anleitung.pdf')
    # addTxtFromFolder(vectordb)
    # addWikiInfos(vectordb, 'chat-gpt')

    # basic testing
    testQuery = "gpt ist cool "
    docs = vectordb.similarity_search(testQuery)
    print("Answer: ")
    print(docs[0].page_content)   
    
    # with score
    docs = vectordb.similarity_search_with_score(testQuery)
    print("\n Answer: ")
    print(docs[0])
