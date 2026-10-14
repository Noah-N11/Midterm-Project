from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

otherf = open("agent-stuff/.api-info", "r")
key= otherf.read()
otherf.close()

MAX_REQUESTS_PER_MIN = 4
DELAY = 60

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    api_key=key
)

instructions = """
You are a helpful and friendly agent which answers questions from {u_input}.
"""

agent = create_agent(
    model = llm,
    system_prompt = instructions
)

u_input = input("Please enter your question here: ")

response = agent.invoke({
"messages": [{"role": "user", "content": u_input}]
})
print(response["messages"][-1].content)