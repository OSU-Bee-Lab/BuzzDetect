import tensorflow_hub as hub
import pandas as pd
from buzzcode.tools import *
from buzzcode.preprocess import *

yamnet_model_handle = 'https://tfhub.dev/google/yamnet/1'
yamnet_model = hub.load(yamnet_model_handle)

def analyze_wav(model, classes, wav_in, frameLength = 500, frameHop = 250):
    audio_data = load_wav_16k_mono(wav_in)
    audio_data_split = tf.signal.frame(audio_data, frameLength*16, frameHop*16, pad_end=True, pad_value=0)

    results = []

    for i, data in enumerate(audio_data_split):
        scores, embeddings, spectrogram = yamnet_model(data)
        result = model(embeddings).numpy()

        class_means = result.mean(axis=0)
        predicted_class_index = class_means.argmax()
        inferred_class = classes[predicted_class_index]

        confidence_score = class_means[predicted_class_index]

        results.append(
            {
                "start" : (i*frameHop)/1000,
                "end" : ((i*frameHop)+frameLength)/1000,
                "classification" : inferred_class,
                "confidence" : confidence_score
            }
        )

    output_df = pd.DataFrame(results)

    return(output_df)

def analyze_mp3_in_place(model, classes, mp3_in, chunkLength_hr = 1, frameLength = 1500, frameHop = 750):
    # make chunk list
    audio_length = librosa.get_duration(path=mp3_in)
    chunk_length = int(60 * 60 * chunkLength_hr)  # in seconds
    chunklist = make_chunklist(audio_length, chunk_length)

    analysis_list = []

    for chunk in chunklist:
        # generate chunk and store path
        chunk_path = take_chunk(chunk, mp3_in)
        chunk_start = chunk[0]

        # analyze chunkfile
        chunk_analysis = analyze_wav(model = model, classes = classes, wav_in = chunk_path, frameLength = frameLength, frameHop = frameHop)
        chunk_analysis["start"] = chunk_analysis["start"] + chunk_start
        chunk_analysis["end"] = chunk_analysis["end"] + chunk_start
        # delete where frame out-runs file? chunk with one frame overlaps?

        # delete chunkfile
        os.remove(chunk_path)

        analysis_list.append(chunk_analysis)

    full_analysis = pd.concat(analysis_list)

    return(full_analysis)



def analyze_mp3_batch(modelname, directory_in ="./audio_in", directory_out ="./output", frameLength = 500, frameHop = 250):
    model = loadUp(modelname)

    # if user leaves directory out as default, store results in model subdirectory of output
    if directory_out == './output':
        directory_out = os.path.join(directory_out, modelname)

    if not os.path.exists(directory_out):
        os.makedirs(directory_out)

    classes = []

    with open(os.path.join("models/", modelname, "classes.txt"), "r") as file:
        # Use a for loop to read each line from the file and append it to the list
        for line in file:
            # Remove the newline character and append the item to the list
            classes.append(line.strip())

    file_list = os.listdir(directory_in)
    r = re.compile('.+\.wav$')
    wav_files = list(filter(r.match, file_list))

    for file_name in wav_files:
        file_path = os.path.join(directory_in, file_name)
        file_output = re.sub(string = file_name, pattern =  r".wav$", repl = "_buzzdetect.txt")
        file_path_out = os.path.join(directory_out, file_output)
        analyze_wav(model = model, wav_in= file_path, path_out = file_path_out, frameLength = frameLength, frameHop = frameHop, classes = classes)