import paramiko
#A seperate file to just grab the data of the vm
#Doesn't use functions from agent.py because that would create an excessive amount of users on vm

para = paramiko.SSHClient()
para.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#hostname is whatever ip, port is ssh (22), username is that of the agent, and key should be the path to your file with private ssh key
para.connect(
    hostname="35.211.54.249",
    port=22,
    username="agent",
    key_filename="agent-stuff/.sshkey"
)

#Uses a try to ensure the connection with vm is closed upon program stopping
try:
    while(True):
        stdin, stdout, stderr = para.exec_command("free -h")
        memory = stdout.read().decode()
        #Grabs the used memory and divides it by the total, mutiplying into a percent
        almost = 100*(float(memory[108:111])/float(memory[96:99]))
        mpercent = ("%.1f" % almost)
        
        stdin, stdout, stderr = para.exec_command("top -b -n 1 | grep %Cpu")
        cpu = stdout.read().decode()
        cpercent = float(cpu[10:13])
        
        stdin, stdout, stderr = para.exec_command("df -h /dev/root")
        disku = stdout.read().decode()
        dpercent = float(disku[83:85])
        
        stdin, stdout, stderr = para.exec_command("sar -n DEV 1 5 --iface=ens4 ")
        netio = stdout.read().decode()
        rx = (netio[1280:1284])
        tx = (netio[1290:1294])

        print(tx, rx, cpercent, mpercent, dpercent)
finally:
    para.close()