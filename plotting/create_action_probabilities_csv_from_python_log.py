import argparse
import re
import csv

def process_file(input_file, output_csv):
    # Extended regular expression to capture the episode, step, action probabilities, and action time
    pattern = re.compile(r"Episode (\d+), Step (\d+), Action Probablities: \[(.*?)\],.*Action time: (\d+\.\d+),.*")

    # Open the output CSV file for writing
    with open(output_csv, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Write headers to the CSV file, including the new episode and step columns
        csvwriter.writerow(['Episode', 'Step', 'Action Time', 'Prob1', 'Prob2', 'Prob3'])

        # Open the input file and read line by line
        with open(input_file, 'r') as file:
            for line in file:
                match = pattern.search(line)
                if match:
                    # Extract episode, step, action probabilities, and action time
                    episode = int(match.group(1))
                    step = int(match.group(2))
                    probabilities = match.group(3).split()
                    action_time = float(match.group(4))
                    
                    # Convert action time to integer (floor)
                    action_time = int(action_time)
                    
                    # Write the extracted values to the CSV, including episode and step
                    csvwriter.writerow([episode, step, action_time] + probabilities)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Process log file to extract action probabilities, times, episode, and step.')
    parser.add_argument('input_file', type=str, help='Input log file path')
    parser.add_argument('output_csv', type=str, help='Output CSV file path')
    
    # Parse arguments
    args = parser.parse_args()

    # Process the file with the provided arguments
    process_file(args.input_file, args.output_csv)

if __name__ == '__main__':
    main()
