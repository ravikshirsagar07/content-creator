from modules.vectorstore import load_vectorstore


def get_retriever():

    vectorstore = load_vectorstore()

    return vectorstore.as_retriever(
        search_kwargs={
            "k": 5
        }
    )