import os
import re
import librosa
from subprocess import Popen
from subprocess import list2cmdline
import pandas as pd
import numpy as np

def make_chunklist(audio_path, chunklength=None, audio_length=None):
    if audio_length is None:
        audio_length = librosa.get_duration(path=audio_path)

    if chunklength is None:
        chunklength_s = audio_length
    else:
        chunklength_s = int(60 * 60 * chunklength)  # in seconds

    if chunklength_s >= audio_length:
        return [(0, audio_length)]

    start_time = 0 - chunklength_s # a bit odd, but makes the while loop an easier read
    end_time = start_time + chunklength_s

    chunklist = []

    while end_time < audio_length:
        start_time += chunklength_s
        end_time += chunklength_s

        # avoids miniscule chunks
        if ((audio_length - end_time) < 30):
            end_time = audio_length

        chunklist.append((start_time, end_time))

    return chunklist

def take_chunk(chunklist, path_in_list, path_out_list, band_low=200):
    commands = []
    for chunk, path_in, path_out in zip(chunklist, path_in_list, path_out_list):
        command = list2cmdline(
            [
                "ffmpeg",
                "-i", path_in,  # Input file
                "-y",  # overwrite any chunks that didn't get deleted (from early interrupts)
                "-ar", "16000",  # Audio sample rate
                "-ac", "1",  # Audio channels
                "-af", "highpass = f = " + str(band_low),
                "-ss", str(chunk[0]),  # Start time
                "-to", str(chunk[1]),  # End time
                "-c:a", "pcm_s16le",  # Audio codec
                path_out  # Output path
            ]
        )

        commands.append(command)

    processes = [Popen(cmd, shell = True) for cmd in commands]

    for p in processes:
        p.wait()

def make_chunk_from_control(control, band_low = 200):
    commands = []
    for r in list(range(0, len(control))):
        row = control.iloc[r]
        commands.append(make_chunk_command(row['path_in'], row['path_chunk'], (row['start'], row['end']), band_low))

    processes = [Popen(cmd, shell=True) for cmd in commands]

    for p in processes:
        p.wait()
