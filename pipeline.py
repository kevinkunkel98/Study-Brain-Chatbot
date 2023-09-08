from dotenv import load_dotenv
import os
from chroma import createDatabase, addTxtFromFolder
from langchain.vectorstores import Chroma 
from langchain.embeddings import HuggingFaceEmbeddings 
from topicExtraction import extract_topics_from_pdfs_lda, extract_topics_from_pdfs_gpt
from scrapeMedium import scrapeLinksToArticles, getArticleText

# Setup
load_dotenv()
db_folder_name = os.getenv('DB_FOLDER_NAME')
pdf_folder_path = os.getenv("PDF_FOLDER_NAME")
proxy_url = os.getenv("OPENAI_PROXY")
api_key = os.getenv("OPENAI_API_KEY")
additional_txt_folder_name = os.getenv('SCRAPE_FOLDER_NAME')
embeddings = HuggingFaceEmbeddings(model_name=os.getenv("HUGGINGFACE_MODEL"))


def initalize_dataPipe(topics='lda', years=["2023"], months=["05"]):
    if not os.path.exists(db_folder_name):
        # create database with already existing pdfs
        createDatabase(pdf_folder_path, embeddings, db_folder_name)    
    #load existing chromadb
    vectordb = Chroma(persist_directory=db_folder_name, embedding_function=embeddings)
    
    if(topics =='lda'):
    # extract topics lda
        df_lda = extract_topics_from_pdfs_lda(pdf_folder_path)
        flat_list = [word for sublist in df_lda['topics'] for word in sublist]
        #print('Topics der pdfs: ' + str(list(set(flat_list))))
    elif(topics =='gpt'):
        # extract topics gpt
        df_gpt = extract_topics_from_pdfs_gpt(pdf_folder_path, proxy_url, api_key)
        flat_list = [word for sublist in df_gpt['topics'] for word in sublist]

    # scrape topics as tags
    articleLinks = []
    tags = list(set(flat_list))
    for tag in tags: 
       articleLinks.extend(scrapeLinksToArticles(tag, years, months))
    articleLinks = set(articleLinks)

    articles = getArticleText(articleLinks, top=20)
    # embed into db
    addTxtFromFolder(vectordb, additional_txt_folder_name)


if __name__ == "__main__":
    initalize_dataPipe()