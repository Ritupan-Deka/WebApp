import speech_recognition as sr
from pydub import AudioSegment
import threading
import queue
import os


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def write_to_file(text, filename):
    with open(filename, "w") as file:  # Use "w" mode to overwrite the file
        file.write(text + " ")


def log_error(message, filename="error_log.txt"):
    with open(filename, "a") as log_file:
        log_file.write(message + "\n")


def recognize_speech(audio, recognizer, filename):
    try:
        text = recognizer.recognize_google(audio)
        write_to_file(text, filename)
    except sr.UnknownValueError:
        log_error("UnknownValueError: Could not understand the audio")
    except sr.RequestError as e:
        error_message = f"API request error: {e}"
        log_error(error_message)
    except Exception as e:
        log_error(f"Unexpected error: {e}")


def audio_listener(audio_queue, recognizer, microphone):
    while True:
        with microphone as source:
            audio = recognizer.listen(source, phrase_time_limit=20)
        audio_queue.put(audio)


def transcriber(audio_queue, recognizer, filename):
    while True:
        audio = audio_queue.get()
        if audio is None:
            break
        recognize_speech(audio, recognizer, filename)
        audio_queue.task_done()


def convert_audio_to_wav(audio_file, wav_file):
    audio = AudioSegment.from_file(audio_file)
    audio.export(wav_file, format="wav")
    print(f"Converted {audio_file} to {wav_file}")


def split_audio_to_chunks(audio_file, chunk_length_ms=60000):
    audio = AudioSegment.from_wav(audio_file)
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i : i + chunk_length_ms]
        chunk_name = f"chunk_{i//chunk_length_ms}.wav"
        chunk.export(chunk_name, format="wav")
        chunks.append(chunk_name)
    return chunks


def transcribe_audio_file(recognizer, audio_chunk):
    with sr.AudioFile(audio_chunk) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Could not understand the audio"
        except sr.RequestError as e:
            return f"Could not request results; {e}"


def live_transcription(filename='itadori.txt'):
    recognizer = sr.Recognizer()
    audio_queue = queue.Queue()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    listener_thread = threading.Thread(
        target=audio_listener, args=(audio_queue, recognizer, microphone)
    )
    listener_thread.daemon = True
    listener_thread.start()

    transcriber_thread = threading.Thread(
        target=transcriber, args=(audio_queue, recognizer, filename)
    )
    transcriber_thread.daemon = True
    transcriber_thread.start()

    while listener_thread.is_alive() and transcriber_thread.is_alive():
        listener_thread.join(timeout=1)
        transcriber_thread.join(timeout=1)


def file_transcription(audio_file, filename='itadori.txt'):
    wav_file = "temp.wav"
    if not audio_file.lower().endswith(".wav"):
        convert_audio_to_wav(audio_file, wav_file)
    else:
        wav_file = audio_file

    chunk_length_ms = 30 * 1000
    chunks = split_audio_to_chunks(wav_file, chunk_length_ms)

    recognizer = sr.Recognizer()

    for chunk in chunks:
        text = transcribe_audio_file(recognizer, chunk)
        with open(filename, "a") as f:
            f.write(text + " ")
        os.remove(chunk)

    if wav_file == "temp.wav" and os.path.exists(wav_file):
        os.remove(wav_file)
        
    
    
