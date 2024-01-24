import logging
import sys
import argparse
import wave
import queue

import homeas

import numpy as np
import sounddevice as sd
import time
from datetime import datetime

parser = argparse.ArgumentParser(description='This is a sample script.')
parser.add_argument('-l', action='store_true', help='List Audio Devices')
parser.add_argument('-w', type=str, help='Process Wave')
parser.add_argument('-log', '--loglevel', type=str, default='info',
                    help='Set the logging level (debug, info, warning, error, critical)')

np.set_printoptions(suppress=True)
# logging.basicConfig(stream=sys.stderr, level=logging.WARNING)


CHUNK = 4096  # number of data points to read at a time
RATE = 44100  # time resolution of the recording device (Hz)
DIV = 32
MIC_DEVICE_INDEX = 6

TONE_A_LENGTH = .8
TONE_A_LENGTH_THRESHOLD = .2
TONE_B_LENGTH = 2.4
TONE_B_LENGTH_THRESHOLD = .2


def list_audio_devices():
    print("List of audio devices and their indices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:  # Check if the device can be used as a microphone
            print(f"Input Device (Microphone) - Index: {i}, Name: {device['name']}")
        else:
            print(f"Output Device (Speaker) - Index: {i}, Name: {device['name']}")


def get_code(freq, codes, threshold):
    dist = {}
    for i in codes:
        dist[i] = abs(i - freq)
    if min(dist.values()) > threshold:
        return 0
    else:
        return codes[min(dist, key=dist.get)]


quik_call_freqs = {360: 1, 338: 2}

tones_counter = 0
tones_open = 0
last_code = 0
listening = False
listening_open = 0

tone_detected = False


def callback(indata, frames, time_info, status):
    if status:
        logging.critical(status)

    process(indata, True, RATE)


first_code_open = False
second_code_open = False
first_code_open_at = None
second_code_open_at = None
last_code = 0

cur_chunk = 0
audio_queue = queue.Queue()
global_wav_name = None


def process(indata, is_realtime, rate):
    global tones_counter, tones_open, last_code, listening, listening_open
    global first_code_open, first_code_open_at, second_code_open, second_code_open_at
    global cur_chunk, audio_queue, tone_detected, global_wav_name

    def get_time():
        if is_realtime:
            return time.time()
        else:
            return (CHUNK / rate) * cur_chunk

    data = np.frombuffer(indata, dtype=np.int16)
    data = data * np.hanning(len(data))

    fft = abs(np.fft.fft(data).real)
    fft = fft[:int(len(fft) / DIV)]

    freq = np.fft.fftfreq(CHUNK, 1.0 / rate)
    freq = freq[:int(len(freq) / DIV)]

    # Find the index of the peak in the full FFT array
    peak_index = np.argmax(fft)

    # Use this index to find the corresponding frequency
    if peak_index < len(freq):
        freq_peak = freq[peak_index] + 1
        code = get_code(freq_peak, quik_call_freqs, 10)
    else:
        code = 0
        logging.info("Peak index out of bounds. Skipping this iteration.")

    audio_queue.put(code)
    if audio_queue.qsize() > (3 // (CHUNK / rate)):
        audio_queue.get()
        queue_list = list(audio_queue.queue)

        a_tone_counter = 0
        for code_read in queue_list[:int((3 // (CHUNK / rate)) // 3)]:
            if code_read == 1:
                a_tone_counter += 1

        a_tone_accuracy = a_tone_counter / ((3 // (CHUNK / rate)) // 3)
        b_tone_counter = 0
        for code_read in queue_list[int(-2 * ((3 // (CHUNK / rate)) // 3)):]:
            if code_read == 2:
                b_tone_counter += 1

        b_tone_accuracy = b_tone_counter / (2 * ((3 // (CHUNK / rate)) // 3))

        if a_tone_accuracy > .8 and b_tone_accuracy > .8:
            logging.info("Tone A : " + str(a_tone_accuracy) + " Tone B : " + str(b_tone_accuracy))
            logging.critical(f"TONE DETECTED @ {datetime.now() if is_realtime else get_time()}")
            logging.info("File" + str(global_wav_name))
            tone_detected = True
            homeas.send(global_wav_name)
            audio_queue = queue.Queue()

    cur_chunk += 1


if __name__ == '__main__':
    args = parser.parse_args()
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(stream=sys.stderr, level=numeric_level)

    if args.l:
        list_audio_devices()
    elif args.w:
        wave_file = args.w
        global_wav_name = wave_file.split('/')[-1]
        wf = wave.open(wave_file, 'rb')
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            logging.warning("Unsupported audio format. Please use a mono WAV file with 16-bit samples at 44100 Hz.")
            wf.close()
            sys.exit(1)
        logging.info("Processing file: " + wave_file)
        data = wf.readframes(CHUNK)
        chunk_duration = (CHUNK / RATE)

        while len(data) > 0:
            # start_time = time.time()
            process(data, False, wf.getframerate())
            data = wf.readframes(CHUNK)
            # logging.debug("Sleeping: " + str(chunk_duration - (start_time - time.time())))
            # time.sleep(chunk_duration - (start_time - time.time()))
        wf.close()

        if tone_detected:
            sys.exit(3)
        else:
            sys.exit(0)
    else:
        with sd.InputStream(callback=callback, channels=1, samplerate=RATE, blocksize=CHUNK, device=MIC_DEVICE_INDEX):
            input("Press Enter to stop...\n")
