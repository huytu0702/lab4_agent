from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv(Path(__file__).resolve().parent / ".env")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

print(llm.invoke("Xin chào").content)
