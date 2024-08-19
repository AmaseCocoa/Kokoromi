import subprocess

subprocess.run("pip install -r requirements.txt", shell=True)
subprocess.run("prisma generate", shell=True)