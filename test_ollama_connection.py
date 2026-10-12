print("STEP 1: Python script started")

from langchain_ollama import ChatOllama

print("STEP 2: LangChain Ollama imported")

model = ChatOllama(
    model="qwen3.5:4b",
    temperature=0,
    num_ctx=2048,
    num_predict=256,
    reasoning=False,
)

print("STEP 3: Sending request to Ollama...")

response = model.invoke("Say hello in one short sentence.")

print("Response object:", repr(response))
print("Response content:", repr(response.content))