from src.database.config import supabase
import bcrypt


def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()  # bcrypt says convert password to the bianry, add some salt and convert into hash , and now convert the binary to the text.

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())  # we dont store teacher password any where instead we store the hash value.

def check_teacher_exists(username):
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0  # basically if true returns the boolean 1

def create_teacher(username, password, name):

    data = {"username": username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data

def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]   # nothing but saying first entered username also there will be only one username
        if check_pass(password, teacher['password']):
            return teacher
    return None


def get_all_students():
    response = supabase.table('students').select("*").execute()
    return response.data


def create_student(new_name, face_embedding=None, voice_embedding=None):

    data = {'name': new_name, 'face_embedding': face_embedding, 'voice_embedding': voice_embedding}
    response = supabase.table("students").insert(data).execute()
    return response.data

def create_subject(subject_code, name, section, teacher_id):
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id): # for the teacher id provided if there are subject id matches then calc their followings
    reponse = supabase.table('subjects').select("*, subject_student(count), attendence_logs(timestamp)").eq("teacher_id", teacher_id).execute()
    subjects = reponse.data

    for sub in subjects:
        sub['total_students'] = sub.get("subject_student", [{}])[0].get('count', 0) if sub.get('subject_student') else 0
        attendence = sub.get('attendence_logs', [])
        unique_sessions = len(set(log['timestamp'] for log in attendence))  # using the set we use only the unique one
        sub['total_classes'] = unique_sessions

        sub.pop('subject_student', None)
        sub.pop('attendence_logs', None)
    return subjects

def enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, 'subject_id': subject_id}
    response = supabase.table('subject_student').insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id, subject_id):
    response = supabase.table('subject_student').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data

def get_student_subjects(student_id):
    response = supabase.table('subject_student').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data

def get_student_attendence(student_id):
    response = supabase.table('attendence_logs').select('*, subjects(*)').eq('student_id', student_id).execute()  # it will have the attendence of every subject
    return response.data

def create_attendence(logs):
        response = supabase.table('attendence_logs').insert(logs).execute()
        return response.data

def get_attendence_for_teacher(teacher_id):
    response = supabase.table('attendence_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()  # Here we collect the info from both attendence_logs table and the subjects as at_log only consist of sub_id not the teacher_id, we take inner to take inner table students into consideration
    return response.data