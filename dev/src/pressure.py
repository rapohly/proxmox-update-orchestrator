import random
import subprocess
import time

while True:

    duration = random.randint(30, 3600)
    vm = random.randint(1, 3)

    subprocess.run([
        "stress-ng",
        "--vm", str(vm),
        "--timeout", f"{duration}s"
    ])

    time.sleep(random.randint(10, 3600))
