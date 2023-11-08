import os
import librosa
from subprocess import Popen
from subprocess import list2cmdline


def make_chunklist(filepath, chunklength=None, audio_length=None):
    if audio_length is None:
        audio_length = librosa.get_duration(path=filepath)

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


def cmd_chunk(path_in, stub_out, chunklist, convert = False, band_low=200):
    extension = os.path.splitext(path_in)[1].lower()
    if extension == ".mp3":
        print("input file is mp3, adding conversion options to ffmpeg call")
        convert = True

        # improvement: automatically detect which conditions are not satisfied
        # also...is there penalty in redundant options? Why not always set them?

    cmdlist = [
        "ffmpeg",
        "-i", path_in,
        '-y',
        "-v", "quiet",
        "-stats"
    ]

    for chunktuple in chunklist:
        path_out = stub_out + "_s" + str(chunktuple[0]) + ".wav"

        cmdlet = [
            "-rf64", "always",
            "-ss", str(chunktuple[0]),
            "-to", str(chunktuple[1])
        ]

        if convert is True:
            cmdlet.extend(
                [
                    "-sample_rate", "16000",  # Audio sample rate
                    "-ac", "1",  # Audio channels
                    "-af", "highpass = f = " + str(band_low),
                    "-c:a", "pcm_s16le"  # Audio codec
                ]
            )

        cmdlet.append(path_out)

        cmdlist.extend(cmdlet)

    return list2cmdline(cmdlist)


def cmd_convert(path_in, path_out, band_low=200):
    cmdlist = [
        "ffmpeg",
        "-i", path_in,
        '-n', # don't overwrite
        "-v", "quiet", # low verbosity
        "-stats",
        "-sample_rate", "16000",  # Audio sample rate
        "-ac", "1",  # Audio channels
        "-af", "highpass = f = " + str(band_low),
        "-c:a", "pcm_s16le"  # Audio codec
        "-rf64", "always",  # use riff64 to allow large files
        path_out
    ]

    return list2cmdline(cmdlist)

def take_chunks(control, band_low = 200):
    commands = []
    for r in list(range(0, len(control))):
        row = control.iloc[r]
        commands.append(cmd_chunk(row['path_in'], row['path_chunk'], (row['start'], row['end']), band_low))

    processes = [Popen(cmd, shell=True) for cmd in commands]

    for p in processes:
        p.wait()
