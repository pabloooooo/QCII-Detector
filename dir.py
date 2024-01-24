import os
import subprocess

# Specify the directory containing the .wav files
directory = 'test'

# Loop through each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.wav'):
        # Construct the full file path
        filepath = os.path.join(directory, filename)

        # Run main.py on the file with the required arguments
        command = ['python', 'main.py', '-w', filepath, '-log', 'warning']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Print the output
        print(f"Results for {filename}:")
        print(result.stdout)
