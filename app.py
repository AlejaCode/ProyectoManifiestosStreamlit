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
import re  # Esto te permite trabajar con expresiones regulares para limpiar los guiones



# Ocultar la barra de herramientas superior (que incluye "Share", "Star", y GitHub)
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# CSS para centrar los botones
st.markdown(
    """
    <style>
    div.stButton > button {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 10px auto; /* Ajustar margen para centrar los botones */
        width: 150px; /* Ajustar el ancho de los botones si es necesario */
    }
    </style>
    """,
    unsafe_allow_html=True
)

def clean_text(text):
    # Reemplazar guiones y otros caracteres similares por espacios
    return re.sub(r'[\-\u2010\u2011\u2012\u2013\u2014\u2015]', ' ', text)


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
        # Limpiar la cadena de texto a buscar (esto es interno, no modifica el texto ingresado por el usuario)
        cleaned_search_text = clean_text(text.lower())

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            # Limpiar el texto extraído del PDF antes de buscar
            page_text = clean_text(page.extract_text().lower())
            # Comparar el texto limpio con el texto buscado
            if cleaned_search_text in page_text:
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
    
#Crea ventana     
@st.dialog("Manifiestos de Importación")

def search_pdf(logo):
    st.write(f"Buscando en {logo}")
    # Campo para ingresar el texto a buscar
    search_text = st.text_input("Por favor, ingresa el texto que deseas buscar")

    col1, col2, col3 = st.columns([3,1,3])
    if st.button("Buscar"):
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
            st.success(f"Se encontraron {len(matching_pdfs)} Manifiestos que contienen el texto específico.")
            for item in matching_pdfs:
                shareable_link = create_shareable_link(item['id'])
                if shareable_link:
                  st.write(f"[{item['name']}]({shareable_link})")
                else:
                  st.warning(f"No se pudo generar un link compartido para {item['name']}")
        else:
             st.warning("No se encontraron PDFs que contengan el texto especificado.")
             
        st.write(f"Buscando '{search_text}'  {logo}")
        # Simulación de búsqueda: actualiza el estado de la sesión con los resultados
        st.session_state.search_result = {"logo": logo, "text": search_text}
        st.session_state.modal_open = True  # Cerrar la ventana modal después de buscar


# Inicializar la sesión para la pantalla de búsqueda
if 'search_screen' not in st.session_state:
    st.session_state['search_screen'] = None

# Título centrado en la parte superior
st.markdown("""
    <h4 style='text-align: center; margin-top: 0px;'>MANIFIESTOS DE IMPORTACIÓN</h4>
    """, unsafe_allow_html=True)

# Mostrar los logos en una fila
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.image("FLY-ENERGY-LOGO.png", use_column_width=False, width=200):
     if st.button("Fly Energy"):
        search_pdf("Fly Energy")
       

with col2:
    if st.image("FLY-SOUND-LOGO.png", use_column_width=False, width=200):
      if st.button("Fly Sound"):
         search_pdf("Fly Sound")
     

with col3:
    if st.image("FLY-TECH-LOGO.png", use_column_width=False, width=200):
       if st.button("Fly Tech"):
          search_pdf("Fly Tech")
      


# Mostrar la pantalla de búsqueda cuando se selecciona un logo
if st.session_state['search_screen']:
    st.markdown(f"<h5 style='font-size:16px;'>Buscar en {st.session_state['search_screen']}</h5>", unsafe_allow_html=True)
  