import streamlit as st
from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card
from src.components.dialog_add_photo import add_photos_dialog
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subjects, get_attendence_for_teacher
from src.components.dialog_share_subject import share_subject_dialog
import time as time
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_attendence_result import attendence_result_dialog
import numpy as np
import pandas as pd
from src.pipelines.face_pipeline import predict_attendence
from src.database.config import supabase
from datetime import datetime
from src.components.dialog_voice_attendence import voice_attendence_dialog

def teacher_screen():

    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type=="login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard(): # after login what should be dislayed
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {teacher_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            st.session_state.pop('teacher_data', None)
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendence'


    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendence' else "tertiary"
        if st.button('Take Attendence',type=type1, width='stretch', icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendence'  # storing or tracking the tab
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Manage Subjects', type=type2, width='stretch', icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'  # storing or tracking the tab
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendence_records' else "tertiary"
        if st.button('Attendence Records',type=type3, width='stretch', icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendence_records'  # storing or tracking the tab
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendence":  # this is to open/render that particular tab
        teacher_tab_take_attendence()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendence_records":
        teacher_tab_attendence_records()

    footer_dashboard()
    
def teacher_tab_take_attendence():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendence')

    if 'attendence_images' not in st.session_state:
        st.session_state.attendence_images = []

    subjects = get_teacher_subjects(teacher_id)
    if not subjects:
        st.warning("You haven't created any subjects yet! Please create one to begin")
        return

    subject_options = {f"{s['name']} - {s['subject_code']}": s['subject_id'] for s in subjects}

    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')

    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))

    with col2:
        if st.button('Add Photos', type='primary', icon=':material/photo_prints:', width='stretch'):
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    if st.session_state.attendence_images:
        st.header('Added Photos')
        gallery_cols = st.columns(4)  #basically create 4 cols to store each image col wise

        for idx, img in enumerate(st.session_state.attendence_images):
            with gallery_cols[idx % 4]:  # trick to place the each image in each diff col like , 01230123....
                st.image(img, width='stretch', caption=f'Photo {idx+1}')
    has_photos = bool(st.session_state.attendence_images)  # writtens true if there exist an image else it writtens false
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button('Clear all photos', width='stretch', type='tertiary', icon=':material/delete:', disabled=not has_photos):
            st.session_state.attendence_images = []
            st.rerun()

    with c2:

        if st.button('Run Face Analysis', width='stretch', type='secondary', icon=':material/analytics:', disabled=not has_photos):
            with st.spinner('Deep scanning classroom photos..'):
                all_detected_ids = {}

                for idx, img in enumerate(st.session_state.attendence_images):
                    img_np = np.array(img.convert('RGB'))
                    detected, _, _ = predict_attendence(img_np)  # detected student id

                    if detected:
                        for sid in detected.keys():
                            student_id = int(sid)

                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")  # return student present in which and all photos(if it should come second time it should be in second image right)

                enrolled_res = supabase.table('subject_student').select("*, students(*)").eq('subject_id', selected_subject_id).execute()
                enrolled_students = enrolled_res.data

                if not enrolled_students:
                    st.warning('No students enrolled in this course')

                else:
                    results, attendence_to_log = [], []

                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                    for node in enrolled_students:
                        student = node['students'] # assigning entire dtable students
                        sources = all_detected_ids.get(int(student['student_id']), []) # storing in which and all photo do the id exist
                        is_present = len(sources) > 0 # id id present in more than 0 photo then the student is present

                        results.append({
                            "Name": student['name'],
                            "ID"  : student['student_id'],
                            "Source": ", ".join(sources) if is_present else "-",
                            "Status": "✅ Present" if is_present else "❌Absent"
                        })

                        attendence_to_log.append({
                            'student_id': student['student_id'],
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': bool(is_present)
                        })

                    attendence_result_dialog(pd.DataFrame(results), attendence_to_log)

    with c3:
        if st.button("Use Voice Attendance", type='primary', width='stretch', icon=":material/mic:"):
            voice_attendence_dialog(selected_subject_id)
    

def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.header('Manage Subjects', width='stretch')
    with col2:
        if st.button('Create New Subjects', width='stretch'):
            create_subject_dialog(teacher_id)

    # LIST all SUBJECTS
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("🫂", "Students", sub['total_students']),
                ("🕰️", "Classes", sub['total_classes']),
            ]
        def share_btn():
            if st.button(f"Share Code: {sub['name']}", key=f"share_{sub['subject_code']}", icon=":material/share:"):
                share_subject_dialog(sub['name'], sub['subject_code'])
            st.space()

        subject_card(
            name = sub['name'],
            code = sub['subject_code'],
            section = sub['section'],
            stats=stats,
            footer_callback=share_btn
        )
    else:
        st.info("NO SUBJECTS FOUND. CREATE ONE ABOVE")
            


  
def teacher_tab_attendence_records():
    st.header('Attemdemce Records')

    teacher_id = st.session_state.teacher_data['teacher_id']  # asprior code is not being rerun it will exist
    records = get_attendence_for_teacher(teacher_id)

    if not records:
        return

    data = []

    for r in records:
        ts = r.get('timestamp')

        data.append({  # hre will collect the data to group by based on timeline and other few steps
            "ts_group" : ts.split(".")[0] if ts else None,   # if there is a milisecond time gap to remove it and consider under the same class.
            "Time" : datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N'A",
            "Subject": r['subjects']['name'],
            "Subject Code":r['subjects']['subject_code'],
            "is_present": bool(r.get('is_present', False))
        })

    df = pd.DataFrame(data)

    summary = (
        df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code'])  # here we will do actual group by for atndnce calc
        .agg(
            Present_Count = ('is_present', 'sum'), # how many ae present
            Total_Count = ('is_present', 'count') # total how many 
        ).reset_index()

    )

    summary['Attendence Stats'] = (  # create a new column to show attndence
        "✅" + summary['Present_Count'].astype(str) + " /"
        + summary['Total_Count'].astype(str) + ' Students'
    )

    display_df = (summary.sort_values(by='ts_group', ascending=False)
                  [['Time', 'Subject', 'Subject Code', 'Attendence Stats']]
                )

    st.dataframe(display_df, width='stretch', hide_index=True)


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name:
        return False, "All Fields are required!"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken"
    if teacher_pass != teacher_pass_confirm:
        return False, "Password doesn't match"

    try: 
        create_teacher(teacher_username, teacher_pass, teacher_name)
        return True, "Successfully Created! Login Now"
    except Exception as e:
        return False, f"Unexpected Error: {e}!"

def login_teacher(username, password):
    if not username or not password:
        return False

    teacher = teacher_login(username, password)

    if teacher:
        st.session_state.user_role = 'teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True
    
    return False

def teacher_screen_login():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()
    
    st.markdown("""
    <h3 style='color:black;text_alignment:center;'>Login using password</h3>
                    """, unsafe_allow_html=True)
    st.space()
    st.space()

    teacher_username = st.text_input("Enter username", placeholder='ajwa')
    teacher_password = st.text_input("Enter password", type='password', placeholder='Enter your password')

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button('Login', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            if login_teacher(teacher_username, teacher_password):
                st.toast("Welcome back!", icon="👋")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username and password combo")
    with btnc2:
        if st.button('Register Instead', type="primary", icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            st.session_state.teacher_login_type = 'register'
            # st.rerun()

    footer_dashboard()


def teacher_screen_register():
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header("Register your teacher profile")

    st.space()
    st.space()

    teacher_username = st.text_input("Enter username", placeholder='ajwa')

    teacher_name = st.text_input("Enter name", placeholder='Mohammed Ajwad')

    teacher_pass = st.text_input("Enter your password", type='password', placeholder='Enter your password')

    teacher_pass_confirm = st.text_input("Confirm your password", type='password', placeholder='Enter your password')

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button('Register now', icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                st.success(message)  # to make the message popup working
                time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)

    with btnc2:
        if st.button('Login Instead', type="primary", icon=':material/passkey:', shortcut='control+enter', width='stretch'):
            st.session_state.teacher_login_type='login'

    footer_dashboard()

