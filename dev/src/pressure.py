import random
import subprocess
import time

while True:

    duration = random.randint(30, 3600)
    #cpu = 1
    vm = 2

    subprocess.run([
        "stress-ng",
    #    "--cpu", str(cpu),
        "--vm", str(vm),
        "--timeout", f"{duration}s"
    ])

    time.sleep(random.randint(10, 3600))
