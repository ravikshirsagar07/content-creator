from langchain_core.output_parsers import StrOutputParser

from modules.retriever import get_retriever
from modules.prompts import CONTENT_PROMPT
from modules.llm import get_llm


def generate_content(
    query,
    content_type,
    tone,
    length,
    model_name="gemini-2.5-flash",
    temperature=0.6,
):

    retriever = get_retriever()

    docs = retriever.invoke(query)

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    llm = get_llm(model_name=model_name, temperature=temperature)

    chain = (
        CONTENT_PROMPT
        | llm
        | StrOutputParser()
    )

    response = chain.invoke(
        {
            "context": context,
            "query": query,
            "content_type": content_type,
            "tone": tone,
            "length": length,
        }
    )

    return response, docs