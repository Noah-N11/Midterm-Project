from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
import paramiko

"""
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    hostname="35.211.54.249",
    port=22,
    key_filename="agent-stuff/.sshkey"
)
client.close()
"""

#Opens a hidden file ".api-info", which has permissions set to 600, and reads the api key within
otherf = open("agent-stuff/.api-info", "r")
key= otherf.read()
otherf.close()

#Some limits on the agent to avoid getting locked out of using it
MAX_REQUESTS_PER_MIN = 4
DELAY = 60

#Defines the information about the llm used for the agent
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    api_key=key
)

#The guidelines for the agent
instructions = """
You are a helpful and friendly agent which answers questions from {u_input}, 
offering if there's anything else you can help with after every response.
"""

#Creates the agent using the previously defined info
agent = create_agent(
    model = llm,
    system_prompt = instructions
)

#Starts the agent with a given input
print("Please enter your question here: ")
while(True):
    u_input = input()
    response = agent.invoke({
        "messages": [{"role": "user", "content": u_input}]
        })
    print(response["messages"][-1].content)