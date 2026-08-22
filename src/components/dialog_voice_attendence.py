import streamlit as st
import pandas as pd
from src.database.config import supabase
from src.components.dialog_attendence_result import show_attendence_result
from src.pipelines.voice_pipeline import process_bulk_audio
from datetime import datetime

@st.dialog('Voice Attendance')
def voice_attendence_dialog(selected_subject_id):
    st.write('Record audio of students saying I am present. Then AI will recognize the students')

    audio_data = None

    audio_data = st.audio_input("Record classroom audio")

    if st.button('Analyze Audio', width='stretch', type='primary'):

        if audio_data is None:
            st.warning("Please record the classroom audio first.")
            return
        
        with st.spinner('Processing Audio data'):
            enrolled_res = supabase.table('subject_student').select("*, students(*)").eq('subject_id', selected_subject_id).execute()
            enrolled_students = enrolled_res.data

            if not enrolled_students:
                st.warning('No students enrolled in this course')
                return
            candidates_dict = {
                s['students']['student_id'] : s['students']['voice_embedding']  #gets stud_id -> voice embedding
                for s in enrolled_students if s['students'].get('voice_embedding')  # check if a student has voic e embedding then in dict

            }
            if not candidates_dict:  # means they dont have anu candidate voice rec
                st.error('No enrolled students have voice profiles registered')
                return
            audio_bytes = audio_data.read()

            detected_scores = process_bulk_audio(audio_bytes, candidates_dict)

            results, attendence_to_log = [], []
            
            current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            for node in enrolled_students:
                student = node['students'] # assigning entire dtable students
                score = detected_scores.get(student['student_id'], 0.0) # storing in which and all photo do the id exist
                is_present = bool(score > 0)  # id id present in more than 0 photo then the student is present

                results.append({
                    "Name": student['name'],
                    "ID"  : student['student_id'],
                    "Source": score if is_present else "-",
                    "Status": "✅ Present" if is_present else "❌Absent"
                })  # for displaying the table

                attendence_to_log.append({
                    'student_id': student['student_id'],
                    'subject_id': selected_subject_id,
                    'timestamp': current_timestamp,
                    'is_present': bool(is_present)
                })  # to give processed data to be stored in db

            st.session_state.voice_attendence_results = (pd.DataFrame(results), attendence_to_log)

    if st.session_state.get('voice_attendence_results'):
        st.divider()
        df_results, logs = st.session_state.voice_attendence_results
        show_attendence_result(df_results, logs)