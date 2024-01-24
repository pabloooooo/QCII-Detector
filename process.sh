#!/bin/bash

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "No arguments provided. Please provide a WAV file."
    exit 1
fi

# Assign the first argument to a variable
input_file="$1"

# Check if the file is a WAV file
if [[ $input_file != *.wav ]]; then
    echo "The provided file is not a WAV file."
    exit 1
fi

# Run the Python script with the WAV file
python3 main.py -w "$input_file"

# Check the exit status and file name
if [ $? -eq 0 ] && [[ $(basename "$FILE_PATH") != 37840* ]]; then
    echo "Deleting file: $FILE_PATH" >> /home/sysadmin/log2.txt
    rm "$FILE_PATH"
else
    echo "File not deleted." >> /home/sysadmin/log2.txt
fi