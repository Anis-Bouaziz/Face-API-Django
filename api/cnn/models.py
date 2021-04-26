import cv2
import tensorflow as tf
import numpy as np

from django.http import JsonResponse




EMOTIONS = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]#fer


def detect_face(img,detector):

    
    
    faces = detector.detect_faces(img)
    result = []
    if faces:
        for face in faces:
            if face['confidence']>0.9:
                x, y, w, h = face['box']
                try:
                    result.append({'box': {
                        "top": x,
                        "left": y,
                        "width": w,
                        "height": h
                    },
                        'landmarks': face['keypoints'],

                    })
                except Exception as e:
                    print(str(e))
    del faces
    
    
    return JsonResponse(result, safe=False)


def predict_emotion(img,detector,emotion_classifier):
    gray_fr = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    result = []
    faces = detector.detect_faces(img)
    if faces:
        for face in faces:
            if face['confidence']>0.9:
                x, y, w, h = face['box']
                fc = gray_fr[y:y+h, x:x+w]
                try:
                    roi = cv2.resize(fc, (48, 48))
                    roi = roi.astype("float") / 255.0
                    roi = tf.keras.preprocessing.image.img_to_array(roi)
                    roi = np.expand_dims(roi, axis=0)
                    preds = emotion_classifier.predict(roi)[0]
                    emotion_probability = np.max(preds)
                    label = EMOTIONS[preds.argmax()]
                    result.append({'box': {
                        "top": x,
                        "left": y,
                        "width": w,
                        "height": h
                    },

                        'emotion': label,
                        'probability': str(emotion_probability)})
                    del roi
                    
                except Exception as e:
                    print(str(e))
    del faces
    del gray_fr
   
    return JsonResponse(result, safe=False)
