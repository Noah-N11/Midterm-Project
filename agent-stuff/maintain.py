from agent import find_memory, find_cpu_usage, find_disk_usage, para

#A seperate file to just grab the data of the vm

#Using the functions from agent, grabs the data and converts it into float percentages
memory = find_memory()
almost = 100*(float(memory[108:111])/float(memory[96:99]))
mpercent = ("%.1f" % almost)
para.close()

cpu = find_cpu_usage()
cpercent = float(cpu[10:13])
para.close()

disku = find_disk_usage()
dpercent = float(disku[83:85])
para.close()
print(mpercent, cpercent, dpercent)