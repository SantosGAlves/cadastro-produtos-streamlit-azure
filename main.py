import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import uuid
import pyodbc
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Credenciais do Blob Storage
blobConnectionString = os.getenv("BLOB_CONNECTION_STRING")
blobContainerName = os.getenv("BLOB_CONTAINER_NAME")
blobAccountName = os.getenv("BLOB_ACCOUNT_NAME")

# Credenciais do SQL Server
SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

# Título do app
st.title("Cadastro de Produtos")

# Campos do formulário
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=['jpg', 'jpeg', 'png', 'JPG'])

# Função para enviar imagem para o Blob Storage
def upload_image_to_blob(file):
    try:
        blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
        container_client = blob_service_client.get_container_client(blobContainerName)
        blob_name = str(uuid.uuid4()) + file.name  # Gera nome único
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(file.read(), overwrite=True)
        image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
        return image_url
    except Exception as e:
        st.error(f"Erro ao enviar imagem para o Blob Storage: {e}")
        return None

# Função para salvar os dados do produto no banco de dados
def save_product_to_sql(name, price, description, image_file):
    if not image_file:
        st.warning("Por favor, envie uma imagem do produto.")
        return False

    image_url = upload_image_to_blob(image_file)
    if not image_url:
        return False

    try:
        connection = pyodbc.connect(
            f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USER};PWD={SQL_PASSWORD};TrustServerCertificate=yes'
        )
        cursor = connection.cursor()
        sql = "INSERT INTO Produtos (nome, preco, descricao, image_url) VALUES (?, ?, ?, ?)"
        cursor.execute(sql, (name, price, description, image_url))
        connection.commit()
        cursor.close()
        connection.close()
        st.success("Produto cadastrado com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao cadastrar produto: {e}")
        return False

# Função para deletar produto
def deletar_produto(produto_id):
    try:
        connection = pyodbc.connect(
            f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USER};PWD={SQL_PASSWORD};TrustServerCertificate=yes'
        )
        cursor = connection.cursor()
        sql = "DELETE FROM Produtos WHERE id = ?"
        cursor.execute(sql, (produto_id,))
        connection.commit()
        cursor.close()
        connection.close()
        st.success(f"Produto ID {produto_id} excluído com sucesso!")
        
        # Manter listagem ativa após exclusão
        st.session_state["mostrar_produtos"] = True
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao excluir produto: {e}")

# Função para listar produtos cadastrados
def listar_produtos():
    try:
        connection = pyodbc.connect(
            f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USER};PWD={SQL_PASSWORD};TrustServerCertificate=yes'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT id, nome, preco, descricao, image_url FROM Produtos")
        produtos = cursor.fetchall()
        cursor.close()
        connection.close()

        if not produtos:
            st.info("Nenhum produto cadastrado.")
            return

        # Exibe produtos
        for produto in produtos:
            with st.container():
                st.markdown(f"**ID:** {produto.id}")
                st.markdown(f"**Nome:** {produto.nome}")
                st.markdown(f"**Preço:** R$ {produto.preco:.2f}")
                st.markdown(f"**Descrição:** {produto.descricao}")
                st.image(produto.image_url, width=200)

                # Botão para excluir o produto
                if st.button(f"Excluir Produto ID {produto.id}", key=f"del_{produto.id}"):
                    deletar_produto(produto.id)
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")

# Botão para cadastrar produto
if st.button("Cadastrar Produto"):
    save_product_to_sql(product_name, product_price, product_description, product_image)

# Cabeçalho da seção de resultados
st.header("Resultado do Cadastro")

# Botão para listar produtos (controlado por estado)
if st.button("Listar Produtos"):
    st.session_state["mostrar_produtos"] = True

# Se o estado de sessão indicar, lista os produtos
if st.session_state.get("mostrar_produtos", False):
    listar_produtos()
