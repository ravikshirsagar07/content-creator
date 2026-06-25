print("DIAGNOSTIC: modules/loader.py is executing!")
import os
from pathlib import Path

from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.word_document import Docx2txtLoader

UPLOAD_FOLDER = "uploads"


def save_uploaded_file(uploaded_file):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = os.path.join(
        UPLOAD_FOLDER,
        uploaded_file.name
    )

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def load_documents(uploaded_files):

    documents = []

    for uploaded_file in uploaded_files:   # <-- Fixed here

        file_path = save_uploaded_file(uploaded_file)

        suffix = Path(file_path).suffix.lower()

        if suffix == ".pdf":
            loader = PyPDFLoader(file_path)

        elif suffix == ".txt":
            loader = TextLoader(
                file_path,
                encoding="utf-8"
            )

        elif suffix == ".docx":
            loader = Docx2txtLoader(file_path)

        else:
            continue

        documents.extend(loader.load())

    return documents

print("DIAGNOSTIC: modules/loader.py loading complete! load_documents is defined:", "load_documents" in globals())