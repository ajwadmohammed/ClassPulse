from resemblyzer import VoiceEncoder, preprocess_wav # preprocess_wav will once again preprocess. 
import numpy as np
import io
import librosa
import streamlit as st

@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()

def get_voice_embeddings(audio_bytes):
    try:
        encoder = load_voice_encoder()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)  # io.BytesIo(audio_bytes) stores those binary audio and store as a file like object in memory, from where it is being loaded by librosa
        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception as e:
        st.error(f"Voice recog error: {e}")
        return None

def identify_speaker(new_embedding, candidates_dict, threshold=0.65):
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():  # checking dot of which is greater with the embedding existing in dict.
        if stored_embedding:
            similarity = np.dot(new_embedding, stored_embedding)
            if similarity > best_score:
                best_score = similarity
                best_sid = sid

    if best_score >= threshold:  # the embedding in dict with the best dot product / score is taken and checked with threshold, if it is reater than the treshold then it is being considered
        return best_sid, best_score

    return None, best_score

# funvtion  t process the bulk audio that is being spoken one by one
def process_bulk_audio(audio_bytes, candidate_dict, threshold=0.65):

    try:
        encoder = load_voice_encoder()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)  # io.BytesIo(audio_bytes) stores those binary audio and store as a file like object in memory, from where it is being loaded by librosa
        segments = librosa.effects.split(audio, top_db=30) # actually right here we may have voices of multiple students that's divide it into the segments and for the better understanding to know whose voice it is, top_dp means whatlevel of voice variation to be detected from

        identified_results = {}

        for start, end in segments:

            if (end-start) < sr * 0.5: # to remove the noise
                continue           # means skip
            segments_audio = audio[start:end]  # will take part where only the audio is present
            wav = preprocess_wav(segments_audio)
            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding, candidate_dict, threshold)

            if sid:
                if sid not in identified_results or score > identified_results[sid]: # for each speaker have the highest matching score
                    identified_results[sid] = score
        return identified_results
    except Exception as e:
        st.error('Bulk process error')
        return {}



