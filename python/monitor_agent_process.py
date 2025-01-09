import psutil
import time
import csv
import sys

def monitor_process(pid, output_file, interval=1):
    try:
        # try to create a psutil.Process instance for the given PID
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        print(f'Process with PID {pid} does not exist.')
        return

    # open csv for writing
    with open(output_file, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # the header
        csv_writer.writerow(['timestamp', 'cpu_usage', 'rss_memory_MB', "vms_memory_MB"])

        print(f'Monitoring process with PID {pid}. Writing to {output_file}.')

        # monitor the process in a loop
        while True:
            try:
                # cpu usage percentage
                cpu_usage = process.cpu_percent(interval=1)

                # memory usage
                memory_info = process.memory_info()
                rss_memory = memory_info.rss / (1024 * 1024)  # convert to MB
                vms_memory = memory_info.vms / (1024 * 1024)  # convert to MB

                # current time
                # timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                timestamp = time.time()

                # write the resource usage to csv
                csv_writer.writerow([timestamp, cpu_usage, rss_memory, vms_memory])
                csv_file.flush()

                # sleep for the specified interval
                time.sleep(interval)

            except psutil.NoSuchProcess:
                print(f'Process with PID {pid} has terminated.')
                break

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python monitor_process.py <PID> <output_file>')
        sys.exit(1)

    pid = int(sys.argv[1])
    output_file = sys.argv[2]

    monitor_process(pid, output_file)
