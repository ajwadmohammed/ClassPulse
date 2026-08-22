

import dlib  # face inda
import numpy as np
import face_recognition_models # contains pretrained models for face recognition
from sklearn.svm import SVC # for classification
import streamlit as st

from src.database.db import get_all_students

@st.cache_resource   # will make below to load only once as it isbeing quite heavy.
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()


    sp = dlib.shape_predictor(  # from the dlib to load the trained facila landmark model on giving the location.
        face_recognition_models.pose_predictor_model_location()   # in model face_recognition where the facial landmark is present. face_reconition_model is a folder.
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec

def get_face_embeddings(image_np): # now here we pass the numpy array of image and call the above function to return the detector, sp, facerec.
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1) # load only the face in the image using the detector, also 1 is because process the image with one angle more-can be used which will increase the perfectness but more cpu and memory utilization might happened.

    # st.write("Image shape:", image_np.shape)
    # st.write("Faces detected by dlib:", len(faces))

    encodings = []

    for face in faces: # for each face detected through the detector in the numpy array converted image.
        shape = sp(image_np, face) # find the landmark
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)  # 128D Embeddings

        encodings.append(np.array(face_descriptor))  # nthing changes just making it to be easier on working with anythig.
    return encodings

@st.cache_resource  # to make it run only once
def get_trained_model():
    X = []
    y = []

    student_db = get_all_students()

    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))

    if len(X) == 0:
        return 0

    clf = SVC(kernel='linear', probability=True, class_weight='balanced') # train the svc so that it could predict which face embedding represent which student during attendence marking. 
    # class weight balanced mean that if one ha 12 image of same person and other with 1 image of a person consider the 1 image person effectively/balnced means just applying th logic here.

    try:
        clf.fit(X, y)
    except ValueError:
        pass

    return {'clf': clf, 'X': X, "y": y}


def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)

def predict_attendence(class_image_np):
    encodings = get_face_embeddings(class_image_np)

    detected_student = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_student, [], len(encodings) # when nobody exists i mean registration == 0

    clf = model_data['clf']
    X_train = model_data['X']  # embeddings
    y_train = model_data['y']  # id's

    all_students = sorted(list(set(y_train)))

    for encoding in encodings:  # this if and  else part will only tells the predict the possibility of id, but not say exact one .Exact is calculated by considering the best score.
        if len(all_students) >= 2:
            predicted_id = int(clf.predict([encoding])[0]) # when there are more than 1 registered students
        else:
            predicted_id = int(all_students[0])

        student_embedding = X_train[y_train.index(predicted_id)]

        best_match_score = np.linalg.norm(student_embedding - encoding)

        resemblence_threshold = 0.6

        if best_match_score <= resemblence_threshold:
            detected_student[predicted_id] = True
    return detected_student, all_students, len(encodings)




