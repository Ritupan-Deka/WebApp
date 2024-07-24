import speech_recognition as sr
from pydub import AudioSegment
import threading
import queue
import os


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def write_to_file(text, filename):
    with open(filename, "a") as file:
        file.write(text + " ")


def log_error(message, filename="error_log.txt"):
    with open(filename, "a") as log_file:
        log_file.write(message + "\n")


def recognize_speech(audio, recognizer, filename):
    try:
        text = recognizer.recognize_google(audio)
        # print(f"Recognized: {text}")
        write_to_file(text, filename)
    except sr.UnknownValueError:
        # print("Could not understand the audio")
        log_error("UnknownValueError: Could not understand the audio")
    except sr.RequestError as e:
        error_message = f"API request error: {e}"
        # print(error_message)
        log_error(error_message)
    except Exception as e:
        # print(f"An error occurred: {e}")
        log_error(f"Unexpected error: {e}")


def audio_listener(audio_queue, recognizer, microphone):
    while True:
        with microphone as source:
            # print("Listening for 20 seconds...")
            audio = recognizer.listen(source, phrase_time_limit=20)
        audio_queue.put(audio)
        # print("Audio segment added to queue")


def transcriber(audio_queue, recognizer, filename):
    while True:
        audio = audio_queue.get()
        if audio is None:
            break
        # print("Processing audio segment from queue")
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


def main():
    clear_console()
    mode = input("Enter '1' for live transcription, '2' for file transcription: ")

    if mode == "1":
        filename = input("Enter filename for live transcription: ") + ".txt"
    elif mode == "2":
        # file_path = input("Enter the path of the audio file: ")
        filename = input("Enter filename for audio transcription: ") + ".txt"
    else:
        print("Invalid mode selected.")
        return

    # Clear the output file at the start
    with open(filename, "w") as file:
        pass

    recognizer = sr.Recognizer()
    if mode == "1":
        audio_queue = queue.Queue()
        microphone = sr.Microphone()

        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                # print("Adjusted for ambient noise. Please start speaking.")

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

        except KeyboardInterrupt:
            print("Stopping transcription...")
            audio_queue.put(None)  
            transcriber_thread.join()
            print("Transcription stopped. Goodbye!")

    elif mode == "2":
        audio_file = input("Enter the path to the audio file (MP3/WAV/etc.): ").strip()
        wav_file = "temp.wav"
        # output_file = input("Enter filename for transcription output: ") + ".txt"

        if not audio_file.lower().endswith(".wav"):
            convert_audio_to_wav(audio_file, wav_file)
        else:
            wav_file = audio_file

        chunk_length_ms = 30 * 1000  
        chunks = split_audio_to_chunks(wav_file, chunk_length_ms)

        recognizer = sr.Recognizer()

        # Transcribe each chunk
        for chunk in chunks:
            # print(f"Transcribing {chunk}...")
            text = transcribe_audio_file(recognizer, chunk)
            with open(filename, "a") as f:
                f.write(text+" ")
            os.remove(chunk)  


        if wav_file == "temp.wav" and os.path.exists(wav_file):
            os.remove(wav_file)
            
            
        # transcribe_audio_file(file_path, recognizer, filename)


if __name__ == "__main__":
    main()
