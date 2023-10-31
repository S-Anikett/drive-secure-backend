import pandas as pd
import cv2
import numpy as np
import mediapipe as mp
import mediapipe as mp
import base64
from fastapi import HTTPException


mp_facemesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
denormalize_coordinates = mp_drawing._normalized_to_pixel_coordinates
all_left_eye_idxs = list(mp_facemesh.FACEMESH_LEFT_EYE)
all_left_eye_idxs = set(np.ravel(all_left_eye_idxs))
all_right_eye_idxs = list(mp_facemesh.FACEMESH_RIGHT_EYE)
all_right_eye_idxs = set(np.ravel(all_right_eye_idxs))
all_idxs = all_left_eye_idxs.union(all_right_eye_idxs)
chosen_left_eye_idxs = [362, 385, 387, 263, 373, 380]
chosen_right_eye_idxs = [33, 160, 158, 133, 153, 144]
all_chosen_idxs = chosen_left_eye_idxs + chosen_right_eye_idxs

IMG_SIZE = 145


def draw_single_image(
    *,
    img_dt,
    img_eye_lmks=None,
    img_eye_lmks_chosen=None,
    face_landmarks=None,
    ts_thickness=1,
    ts_circle_radius=2,
    lmk_circle_radius=3,
    name="1"
):
    image_drawing_tool = img_dt
    image_eye_lmks = img_dt.copy() if img_eye_lmks is None else img_eye_lmks
    connections_drawing_spec = mp_drawing.DrawingSpec(
        thickness=ts_thickness, circle_radius=ts_circle_radius, color=(255, 255, 255)
    )
    mp_drawing.draw_landmarks(
        image=image_drawing_tool,
        landmark_list=face_landmarks,
        connections=mp_facemesh.FACEMESH_TESSELATION,
        landmark_drawing_spec=None,
        connection_drawing_spec=connections_drawing_spec,
    )
    landmarks = face_landmarks.landmark
    for landmark_idx, landmark in enumerate(landmarks):
        if landmark_idx in all_idxs:
            pred_cord = denormalize_coordinates(landmark.x, landmark.y, imgW, imgH)
            cv2.circle(
                image_eye_lmks, pred_cord, lmk_circle_radius, (255, 255, 255), -1
            )

        if landmark_idx in all_chosen_idxs:
            pred_cord = denormalize_coordinates(landmark.x, landmark.y, imgW, imgH)
            cv2.circle(
                img_eye_lmks_chosen, pred_cord, lmk_circle_radius, (255, 255, 255), -1
            )
    resized_array = cv2.resize(image_drawing_tool, (IMG_SIZE, IMG_SIZE))
    return resized_array


imgH, imgW, _ = 0, 0, 0


def landmarks_single_image(image):
    resized_array = []
    IMG_SIZE = 145
    image = np.ascontiguousarray(image)
    imgH, imgW, _ = image.shape
    with mp_facemesh.FaceMesh(
        static_image_mode=True,  # Default=False
        max_num_faces=1,  # Default=1
        refine_landmarks=False,  # Default=False
        min_detection_confidence=0.5,  # Default=0.5
        min_tracking_confidence=0.5,
    ) as face_mesh:
        results = face_mesh.process(image)
        if results.multi_face_landmarks:
            for face_id, face_landmarks in enumerate(results.multi_face_landmarks):
                resized_array = draw_single_image(
                    img_dt=image.copy(), face_landmarks=face_landmarks
                )
        return resized_array


def preprocess_image(
    image_string,
    face_cas_path="app/src/machine_learning_models/haarcascade_frontalface_default.xml",
):
    IMG_SIZE = 145
    try:
        binary_data = base64.b64decode(image_string)
        binary_array = np.frombuffer(binary_data, np.uint8)
        image_array = cv2.imdecode(binary_array, cv2.IMREAD_COLOR)
    except Exception as e:
        raise HTTPException(status_code=400, detail="image string is not valid")

    angle = 270
    height, width = image_array.shape[:2]
    rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
    rotated_image = cv2.warpAffine(image_array, rotation_matrix, (width, height))

    # output_path = "output_image.png"
    # cv2.imwrite(output_path, rotated_image)
    face_cascade = cv2.CascadeClassifier(face_cas_path)
    faces = face_cascade.detectMultiScale(rotated_image, 1.3, 5)

    if len(faces) == 0:
        return {"detail": "face not found"}
    for x, y, w, h in faces:
        img = cv2.rectangle(rotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        roi_color = img[y : y + h, x : x + w]
        land_face_array = landmarks_single_image(roi_color)
        if len(land_face_array) > 0:
            return land_face_array
    return {"detail": "landmarks not configurable"}
