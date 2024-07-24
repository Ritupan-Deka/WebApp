# from django.shortcuts import render
# from django.http import JsonResponse
# from .forms import AudioUploadForm
# import speech_recognition as sr
# from pydub import AudioSegment
# import os

# def home(request):
#     return render(request, 'speech_app/home.html')

# def convert_audio_to_wav(audio_file, wav_file):
#     audio = AudioSegment.from_file(audio_file)
#     audio.export(wav_file, format="wav")

# def split_audio_to_chunks(audio_file, chunk_length_ms=60000, ):
#     audio = AudioSegment.from_wav(audio_file)
#     path = "KOTHA/media"
#     chunks = []
#     for i in range(0, len(audio), chunk_length_ms):
#         chunk = audio[i : i + chunk_length_ms]
#         chunk_name =  f"chunk_{i//chunk_length_ms}.wav"
#         chunk.export(chunk_name, format="wav")
#         chunks.append(chunk_name)
#     return chunks

# def transcribe_audio_file(recognizer, audio_chunk):
#     with sr.AudioFile(audio_chunk) as source:
#         audio_data = recognizer.record(source)
#         try:
#             text = recognizer.recognize_google(audio_data)
#             return text
#         except sr.UnknownValueError:
#             return "Could not understand the audio"
#         except sr.RequestError as e:
#             return f"Could not request results; {e}"

# def recorded(request):
#     transcript_text = ""
#     if request.method == 'POST':
#         form = AudioUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             audio_file = form.cleaned_data['audio_file']
#             file_path = 'media/' + audio_file.name
#             os.makedirs(os.path.dirname(file_path), exist_ok=True)
#             with open(file_path, 'wb+') as destination:
#                 for chunk in audio_file.chunks():
#                     destination.write(chunk)

#             recognizer = sr.Recognizer()
#             wav_file = file_path
#             if not audio_file.name.lower().endswith(".wav"):
#                 temp_wav_file = "media/temp.wav"
#                 convert_audio_to_wav(wav_file, temp_wav_file)
#                 wav_file = temp_wav_file

#             chunk_length_ms = 30 * 1000  # 30 seconds
#             chunks = split_audio_to_chunks(wav_file, chunk_length_ms)

#             transcript_text = ""
#             for chunk in chunks:
#                 text = transcribe_audio_file(recognizer, chunk)
#                 transcript_text += text + " "
#                 os.remove(chunk)
#                 # return render(request, 'speech_app/record.html', {'form': form, 'transcript': transcript_text})
#                 # return render(request, JsonResponse({'transcript': transcript_text}))


#             if wav_file == "media/temp.wav" and os.path.exists(wav_file):
#                 os.remove(wav_file)

#             return JsonResponse({'transcript': transcript_text})

#     else:
#         form = AudioUploadForm()

#     return render(request, 'speech_app/record.html', {'form': form, 'transcript': transcript_text})





import os
import speech_recognition as sr
from pydub import AudioSegment
from django.shortcuts import render
from django.http import StreamingHttpResponse
from .forms import AudioUploadForm

def convert_audio_to_wav(audio_file, wav_file):
    audio = AudioSegment.from_file(audio_file)
    audio.export(wav_file, format="wav")

def split_audio_to_chunks(audio_file, chunk_length_ms=60000, chunk_dir="media/chunks"):
    audio = AudioSegment.from_wav(audio_file)
    os.makedirs(chunk_dir, exist_ok=True)  # Ensure the directory exists
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i: i + chunk_length_ms]
        chunk_name = os.path.join(chunk_dir, f"chunk_{i // chunk_length_ms}.wav")
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


def generate_transcript(chunks, recognizer):
    for chunk in chunks:
        cnt=1
        while cnt<2:
            cnt= cnt+1
            text = ' '
        text = transcribe_audio_file(recognizer, chunk)
        yield f"{text} "
        os.remove(chunk)

def recorded(request):
    if request.method == 'POST':
        form = AudioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            audio_file = form.cleaned_data['audio_file']
            file_path = 'media/' + audio_file.name
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            recognizer = sr.Recognizer()
            wav_file = file_path
            if not audio_file.name.lower().endswith(".wav"):
                temp_wav_file = "media/temp.wav"
                convert_audio_to_wav(wav_file, temp_wav_file)
                wav_file = temp_wav_file

            chunk_length_ms = 30 * 1000  # 30 seconds
            chunk_dir = "media/chunks"  # Define the directory for chunks
            chunks = split_audio_to_chunks(wav_file, chunk_length_ms, chunk_dir)

            response = StreamingHttpResponse(generate_transcript(chunks, recognizer), content_type="text/plain")
            response['X-Accel-Buffering'] = 'no'  # Disable buffering for real-time updates
            return response

    else:
        form = AudioUploadForm()

    return render(request, 'speech_app/record.html', {'form': form})

def home(request):
    return render(request, 'speech_app/home.html')



