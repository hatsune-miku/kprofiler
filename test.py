import psutil


def get_process_cpu_percent(process_name):
    # Get all processes
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            # Check if this is the process we are looking for
            if proc.info["name"] == process_name:
                # Get process by PID
                process = psutil.Process(proc.info["pid"])
                # Calculate CPU usage over a short interval
                process.cpu_percent()
                return process.cpu_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None


if __name__ == "__main__":
    process_name = "Taskmgr.exe"  # Replace with the name of your process
    cpu_percent = get_process_cpu_percent(process_name)
    if cpu_percent is not None:
        print(f"CPU usage of {process_name}: {cpu_percent}%")
    else:
        print(f"Process {process_name} not found.")
