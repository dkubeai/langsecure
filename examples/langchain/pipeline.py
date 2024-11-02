from langchain_community.document_loaders import PyPDFLoader
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain import hub

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
embedding = OpenAIEmbeddings()
#llm = OllamaLLM(model="phi3.5")
#embedding = OllamaEmbeddings(model="nomic-embed-text:latest")

file_path = "../data/3f5ee243547dee91fbd053c1c4a845aa-Paper.pdf"
loader = PyPDFLoader(file_path)

docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
vectorstore = InMemoryVectorStore.from_documents(documents=splits, embedding=embedding)

retriever = vectorstore.as_retriever()

prompt = hub.pull("rlm/rag-prompt")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

from langsecure import Langsecure
from langsecure.langchain import RunnableLangsecure
langsecure = RunnableLangsecure(Langsecure(policy_store="default"))

rag_chain = (
    langsecure
    | {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

response = rag_chain.invoke("How can I cook an apple pie?")
print(response)
