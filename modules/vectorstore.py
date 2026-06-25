import os
import shutil

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from modules.splitter import split_documents

VECTOR_DB = "vectorstore"

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def create_vectorstore(documents, overwrite=True):

    chunks = split_documents(documents)

    if overwrite:
        # Try deleting collection first to avoid Windows file locks
        try:
            vectordb = load_vectorstore()
            vectordb.delete_collection()
        except Exception:
            pass

        if os.path.exists(VECTOR_DB):
            try:
                shutil.rmtree(VECTOR_DB)
            except Exception:
                pass

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=VECTOR_DB
    )

    return vectordb


def load_vectorstore():

    return Chroma(
        persist_directory=VECTOR_DB,
        embedding_function=embedding_model
    )


def is_vectorstore_empty():
    """Checks if the vector store directory is empty or does not contain records."""
    if not os.path.exists(VECTOR_DB):
        return True
    if not os.listdir(VECTOR_DB):
        return True
    try:
        db = load_vectorstore()
        col = db._collection
        if col is None or col.count() == 0:
            return True
        return False
    except Exception:
        return True