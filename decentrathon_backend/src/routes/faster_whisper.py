import gc
import whisperx
from whisperx.asr import WhisperModel
from moviepy.editor import VideoFileClip

from ..config import YOUR_HF_TOKEN


def convert_mp4_to_mp3(mp4_file_path, mp3_file_path, sample_rate=16000):
     # Load the video file
    video = VideoFileClip(mp4_file_path)
    
    # Extract the audio and write it to an MP3 file with the specified sample rate
    video.audio.write_audiofile(mp3_file_path, fps=sample_rate)


def get_trained_model(model_dir, device="cpu", compute_type="int8",):
    return WhisperModel(model_dir, device=device, compute_type=compute_type)

# Initialize and load Whisper model from a saved path or Hugging Face
def load_whisper_model(model_dir, device="cpu", compute_type="int8", language="ru"):

    model = whisperx.load_model(
        "large-v3", 
        device, 
        compute_type=compute_type, 
        language=language,
        model=get_trained_model(model_dir, device=device, compute_type=compute_type)
    )
    return model

# Load audio file for transcription
def load_audio_file(audio_file):
    return whisperx.load_audio(audio_file)

# Transcribe the audio file
def transcribe_audio(model, audio, batch_size=4, language="ru"):
    return model.transcribe(audio, batch_size=batch_size, language=language)

# Align the transcription
def align_transcription(result, audio, device="cpu"):
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    # cleanup_resources([model_a])
    return aligned_result

# Perform diarization and assign speaker labels
def diarize_and_assign_speakers(audio, result, num_speakers=None, min_speakers=None, max_speakers=None, hf_token="", device="cpu"):
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
    diarize_segments = diarize_model(audio, num_speakers=num_speakers, min_speakers=min_speakers, max_speakers=max_speakers)
    result_with_speakers = whisperx.assign_word_speakers(diarize_segments, result)
    return diarize_segments, result_with_speakers

# Cleanup GPU and model resources
def cleanup_resources(models):
    for model in models:
        del model
    gc.collect()
    import torch
    torch.cpu.empty_cache()

# Main pipeline to run the whole process
def speech_to_text_pipeline(audio_file, model_dir, hf_token="", device="cpu", batch_size=4, compute_type="int8", language="ru"):
    # Load the Whisper model
    model = load_whisper_model(model_dir, device=device, compute_type=compute_type, language=language)

    # Load and transcribe audio
    audio = load_audio_file(audio_file)
    transcription_result = transcribe_audio(model, audio, batch_size=batch_size, language=language)
    #print(transcription_result["segments"])  # Before alignment

    # Clean up Whisper model if needed
    # cleanup_resources([model])

    # Align transcription
    aligned_result = align_transcription(transcription_result, audio, device=device)
    # print(aligned_result["segments"])  # After alignment

    # Diarization and speaker assignment
    diarize_segments, final_result = diarize_and_assign_speakers(audio, aligned_result, hf_token=hf_token, device=device)
    #print(diarize_segments)
    #print(final_result["segments"])  # After speaker assignment

    return final_result
