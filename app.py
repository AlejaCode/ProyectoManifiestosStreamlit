import os
import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account
import io
import PyPDF2
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import tempfile

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la clave de encriptación
encryption_key = os.getenv('ENCRYPTION_KEY').encode()
fernet = Fernet(encryption_key)

# Leer el archivo de credenciales encriptado
with open('project1-39350-fe86069a4f59.encrypted', 'rb') as encrypted_file:
    encrypted_data = encrypted_file.read()

# Desencriptar el archivo
decrypted_data = fernet.decrypt(encrypted_data)    

# Guardar temporalmente el archivo desencriptado en el sistema
with open('/tmp/project1-39350-fe86069a4f59.json', 'wb') as decrypted_file:
    decrypted_file.write(decrypted_data)

# Configuración de Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# Usar el archivo desencriptado para obtener las credenciales
creds = service_account.Credentials.from_service_account_file(
    '/tmp/project1-39350-fe86069a4f59.json', scopes=SCOPES)

service = build('drive', 'v3', credentials=creds)
folder_id = os.getenv('FOLDER_ID')

# Función para buscar texto en PDFs
def search_text_in_pdf(pdf_file_id, text):
    try:
        request = service.files().get_media(fileId=pdf_file_id)
        pdf_data = io.BytesIO()
        downloader = MediaIoBaseDownload(pdf_data, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        pdf_data.seek(0)
        reader = PyPDF2.PdfReader(pdf_data)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            if text.lower() in page.extract_text().lower():
                return True
    except Exception as e:
        st.error(f"Error al buscar en el PDF {pdf_file_id}: {e}")
        return False
    return False

# Función para crear enlace compartido
def create_shareable_link(file_id):
    try:
        request_body = {
            'role': 'reader',
            'type': 'anyone'
        }
        response = service.permissions().create(
            fileId=file_id,
            body=request_body
        ).execute()
        link = service.files().get(fileId=file_id, fields='webViewLink').execute()
        return link.get('webViewLink')
    except Exception as e:
        st.error(f"Error creating shareable link for file {file_id}: {e}")
        return None
    
col1, col2 = st.columns(2)
with col1:
    # logo de la empresa
    st.image(".\logo.png", width=300)

with col2: 
    # Streamlit UI
    st.write("   ")
    st.write("   ")
    st.title("MANIFIESTOS DE IMPORTACION")


# Campo para ingresar el texto a buscar
search_text = st.text_input("Por favor, ingresa el texto que deseas buscar")

col1, col2, col3 = st.columns([3,1,3])
if col2.button("Buscar"):
    # Listar archivos PDF en la carpeta de Google Drive
    results = service.files().list(q=f"'{folder_id}' in parents",
                                   spaces='drive',
                                   fields='nextPageToken, files(id, name)').execute()
    items = results.get('files', [])

    matching_pdfs = []
    for item in items:
        if item['name'].endswith('.pdf'):
            if search_text_in_pdf(item['id'], search_text):
                matching_pdfs.append(item)

    if matching_pdfs:
        st.success(f"Se encontraron {len(matching_pdfs)} PDFs que contienen el texto específico.")
        for item in matching_pdfs:
            shareable_link = create_shareable_link(item['id'])
            if shareable_link:
                st.write(f"[{item['name']}]({shareable_link})")
            else:
                st.warning(f"No se pudo generar un link compartido para {item['name']}")
    else:
        st.warning("No se encontraron PDFs que contengan el texto especificado.")
