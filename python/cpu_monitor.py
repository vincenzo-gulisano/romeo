import subprocess
import re
import java_threads as jt
import sys
import re
import argparse
import psutil
import threading
import time
from confluent_kafka import Producer, KafkaError
import os
import csv


class KafkaActionsProducer:
    def __init__(self, bootstrap_servers='michelangelo.cse.chalmers.se:9092', actions_topic='stats'):
        self.bootstrap_servers = bootstrap_servers
        self.actions_topic = actions_topic
        self.producer = Producer({'bootstrap.servers': self.bootstrap_servers})

    def send_stat(self,stat):
        self.producer.produce(self.actions_topic, key=str(time.time()), value=stat)
        self.producer.flush()


def monitor_cpu(proc,kafka_actions_producer,thread_dict, output_folder):

    
    # Create a dictionary to store CPU usage for each thread
    cpu_usage = {thread_id: [] for thread_id in thread_dict.values()}

    while True:

        threads_cpu = {}
        total_percent = proc.cpu_percent(interval=1)
        total_time = sum(proc.cpu_times())
        for t in proc.threads():
            threads_cpu[psutil.Process(t.id).name()]=total_percent * ((t.system_time + t.user_time)/total_time)
            # return [('%s %s %s' % (total_percent * ((t.system_time + t.user_time)/total_time), t.id, psutil.Process(t.id).name())) for t in p.threads()]


        # Iterate through the specified thread pairs
        for string_id, thread_id in thread_dict.items():
            try:
                # Get CPU usage percentage for the thread
                # cpu_percent = psutil.Process(int(thread_id)).cpu_percent(interval=1)

                # Run top as a subprocess to get per-thread CPU usage
                # command = f'top -H -n 1 -b -p {thread_id} | grep {thread_id} | awk \'{{print $9}}\''
                cpu_percent = threads_cpu[string_id]
                cpu_usage[thread_id].append(cpu_percent)

            except psutil.NoSuchProcess:
                # Handle the case where the process doesn't exist
                cpu_usage[thread_id].append(None)

            # Get current time in milliseconds
            timestamp_ms = int(time.time())

            # Print the CPU usage for the thread
            # print(f"Thread ID {thread_id}, StringID {string_id}: {cpu_percent}% CPU usage")
            # kafka_actions_producer.send_stat(f"{timestamp_ms},{string_id}-cpu,{cpu_percent}")

            # Create a CSV file for each thread_name
            csv_file_path = os.path.join(output_folder, f"{string_id}_cpu_data.csv")
            with open(csv_file_path, 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([timestamp_ms, cpu_percent])

        # time.sleep(1)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Monitor threads CPU')
    parser.add_argument('JVM_PID', type=int, help='The PID of the JVM to be inspected')
    parser.add_argument('output_folder', type=str, help='Folder to write CSV files')
    
    # Print the raw command-line arguments
    print("Raw Arguments:", sys.argv)

    args = parser.parse_args()

    thread_names_to_catch = ['in','agg','out']
    thread_ids = {}

    proc = psutil.Process(int(args.JVM_PID))


    thread_pids = jt.get_jvm_thread_pids(args.JVM_PID)
    for pid, thread_name in sorted(thread_pids.items()):
        if thread_name in thread_names_to_catch:
            print(f'{thread_name[:79]:<80}|{pid:<10}')
            thread_ids[thread_name]= pid

    kafka_actions_producer = KafkaActionsProducer()

    # Create a separate thread to monitor CPU usage
    monitor_thread = threading.Thread(target=monitor_cpu, args=(proc,kafka_actions_producer,thread_ids,args.output_folder,), daemon=True)
    monitor_thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass