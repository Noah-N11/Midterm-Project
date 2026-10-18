from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool
import paramiko

#A variable to be used later to check whether the agent used a tool
checkvar = False

para = paramiko.SSHClient()
para.set_missing_host_key_policy(paramiko.AutoAddPolicy())
para.connect(
    hostname="35.211.54.249",
    port=22,
    username="agent",
    key_filename="agent-stuff/.sshkey"
)
para.close()


#Opens a hidden file ".api-info", which has permissions set to 600, and reads the api key within
otherf = open("agent-stuff/.api-info", "r")
key= otherf.read()
otherf.close()

#Some limits on the agent to avoid getting locked out of using it
MAX_REQUESTS_PER_MIN = 4
DELAY = 60


def find_memory():
    """Finds the memory usage of the vm"""
    para = paramiko.SSHClient()
    para.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    para.connect(
        hostname="35.211.54.249",
        port=22,
        username="agent",
        key_filename="agent-stuff/.sshkey"
    )
    checkvar = True
    stdin, stdout, stderr = para.exec_command("free -h")
    return (stdout.read().decode())


def find_cpu_usage():
    """Finds the cpu usage of the vm"""
    para = paramiko.SSHClient()
    para.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    para.connect(
        hostname="35.211.54.249",
        port=22,
        username="agent",
        key_filename="agent-stuff/.sshkey"
    )
    checkvar = True
    stdin, stdout, stderr = para.exec_command("top -n 1 | grep %Cpu")
    return (stdout.read().decode())


def find_disk_usage():
    """Finds the disk usage of root on the vm"""
    para = paramiko.SSHClient()
    para.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    para.connect(
        hostname="35.211.54.249",
        port=22,
        username="agent",
        key_filename="agent-stuff/.sshkey"
    )
    checkvar = True
    stdin, stdout, stderr = para.exec_command("df -h /dev/root")
    return (stdout.read().decode())

tools = [find_memory, find_cpu_usage, find_disk_usage]
#Defines the information about the llm used for the agent
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    api_key=key
)

#The guidelines for the agent
instructions = """
You are a helpful and friendly agent which answers questions from {u_input}, 
using the tools {tools} to answer about the ubuntu vm.
"""

#Creates the agent using the previously defined info
agent = create_agent(
    tools = tools,
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
    #If a tool was used, close the connection to the vm and set the check back to false 
    if(checkvar):
        para.close()
        checkvar = False