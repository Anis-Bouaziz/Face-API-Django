from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http import JsonResponse,StreamingHttpResponse,HttpResponseServerError
import cv2
import numpy as np
import base64
import json
import requests
#from api.camera import VideoCamera
from django.views.decorators import gzip
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django import forms
import tensorflow as tf
from face_API.face.detection.model import RetinaFace
from face_API.face.emotions.model import Xception
from face_API.face.mask.model import Mask_detection
from face_API.face.verification.model import FaceVerif



#Load Models
Retina=RetinaFace()
emotion_classifier=Xception(Retina)
mask_classifier=Mask_detection(Retina)
verif= FaceVerif(Retina)   


def index(request):
    return render(request, 'face_API/index.html')

@csrf_exempt
def faces(request):
    if len(request.FILES)==0:
        return HttpResponse(" Please Choose a file",status=404)
    uploaded_file = request.FILES['file']
    
    content_type = uploaded_file.content_type.split('/')[0]
    if content_type in settings.UPLOAD_EXTENSIONS:
        if uploaded_file.size > settings.MAX_CONTENT_LENGTH:
            return HttpResponse(('Please keep filesize under %s. Current filesize %s') % (filesizeformat(settings.MAX_CONTENT_LENGTH), filesizeformat(uploaded_file.size)),status=500)
    else:
        return HttpResponse('File type is not supported',status=500)
    pass
    img_raw = cv2.imdecode(np.fromstring(uploaded_file.read(),np.uint8), cv2.IMREAD_COLOR)
    img=Retina.draw(img_raw)
    img = image_resize(img_raw, width=600)
    _, jpeg = cv2.imencode('.jpg', img)
    img = base64.encodebytes(jpeg.tobytes())
    json=Retina.json(img_raw)
    context = {'image': img.decode('utf-8'), 'json':json,'total':len(json)}
    return JsonResponse(context, safe=False)

@csrf_exempt
def emotion(request):
    
    if len(request.FILES)==0:
        return HttpResponse(" Please Choose a file",status=404)
    uploaded_file = request.FILES['file']
    content_type = uploaded_file.content_type.split('/')[0]
    if content_type in settings.UPLOAD_EXTENSIONS:
        if uploaded_file.size > settings.MAX_CONTENT_LENGTH:
            return HttpResponse(('Please keep filesize under %s. Current filesize %s') % (filesizeformat(settings.MAX_CONTENT_LENGTH), filesizeformat(uploaded_file.size)),status=500)
    else:
        return HttpResponse('File type is not supported',status=500)
    pass
    
    img_raw = cv2.imdecode(np.fromstring(uploaded_file.read(),
                                     np.uint8), cv2.IMREAD_UNCHANGED)
    img=emotion_classifier.draw(img_raw)
    img = image_resize(img_raw, width=600)
    _, jpeg = cv2.imencode('.jpg', img)
    img = base64.encodebytes(jpeg.tobytes())
    json=emotion_classifier.json(img_raw)
    context = {'image': img.decode('utf-8'), 'json': json,'total':len(json)}
    return JsonResponse(context, safe=False)

@csrf_exempt
def detect_mask(request):
       
    if len(request.FILES)==0:
        return HttpResponse(" Please Choose a file",status=404)
    uploaded_file = request.FILES['file']
    content_type = uploaded_file.content_type.split('/')[0]
    if content_type in settings.UPLOAD_EXTENSIONS:
        if uploaded_file.size > settings.MAX_CONTENT_LENGTH:
            return HttpResponse(('Please keep filesize under %s. Current filesize %s') % (filesizeformat(settings.MAX_CONTENT_LENGTH), filesizeformat(uploaded_file.size)),status=500)
    else:
        return HttpResponse('File type is not supported',status=500)
    pass
    
    img_raw = cv2.imdecode(np.fromstring(uploaded_file.read(),
                                     np.uint8), cv2.IMREAD_UNCHANGED)
    img=mask_classifier.draw(img_raw)
    img = image_resize(img_raw, width=600)
    _, jpeg = cv2.imencode('.jpg', img)
    img = base64.encodebytes(jpeg.tobytes())
    json=mask_classifier.json(img_raw)
    context = {'image': img.decode('utf-8'), 'json': json,'total':len(json)}

    return JsonResponse(context, safe=False)

@csrf_exempt
def verifyFaces(request):
    if len(request.FILES)!=2:
            return HttpResponse(" Please Choose 2 Images",status=404)
    uploaded_file1 = request.FILES['file']
    uploaded_file2 = request.FILES['file2']
    
    content_type = uploaded_file1.content_type.split('/')[0]
    content_type2=uploaded_file2.content_type.split('/')[0]
    if (content_type in settings.UPLOAD_EXTENSIONS) and  (content_type2 in settings.UPLOAD_EXTENSIONS):
        if uploaded_file1.size > settings.MAX_CONTENT_LENGTH:
            return HttpResponse(('Please keep filesize under %s. Current filesize %s') % (filesizeformat(settings.MAX_CONTENT_LENGTH), filesizeformat(uploaded_file1.size)),status=500)
        if uploaded_file2.size > settings.MAX_CONTENT_LENGTH:
            return HttpResponse(('Please keep filesize under %s. Current filesize %s') % (filesizeformat(settings.MAX_CONTENT_LENGTH), filesizeformat(uploaded_file2.size)),status=500)
    else:
        return HttpResponse('File type is not supported',status=500)
    pass
    img_raw1 = cv2.imdecode(np.fromstring(uploaded_file1.read(),
                                        np.uint8), cv2.IMREAD_COLOR)
    img_raw2 = cv2.imdecode(np.fromstring(uploaded_file2.read(),
                                        np.uint8), cv2.IMREAD_COLOR)

    img_height_raw1, img_width_raw1, _ = img_raw1.shape
    img1,img2=verif.draw(img_raw1,img_raw2)
    
    img1 = image_resize(img_raw1, width=600)
    _, jpeg1 = cv2.imencode('.jpg', img1)
    img1 = base64.encodebytes(jpeg1.tobytes())
    img2 = image_resize(img_raw2, width=600)
    _, jpeg2 = cv2.imencode('.jpg', img2)
    img2 = base64.encodebytes(jpeg2.tobytes())
    
    json=verif.json(img_raw1,img_raw2)
    context = {'image1': img1.decode('utf-8'),'image2':  img2.decode('utf-8'),'json':json}
    return JsonResponse(context, safe=False)







###########################CAMERA#######################################
def gen(camera):
    
    while camera.grabbed:
        
        frame = camera.get_frame()
        yield(b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    return HttpResponse(200)
@csrf_exempt
@gzip.gzip_page
def camera(request): 
    camera=VideoCamera()
    if camera.video.isOpened():
        
        return StreamingHttpResponse(gen(camera),content_type="multipart/x-mixed-replace;boundary=frame")
         
    else : camera.video.release()
@csrf_exempt 
def OpenCamera(request):
    return render(request, 'face_API/camera.html')   
@csrf_exempt  
def CloseCamera(request):
    if request.POST['cam']=='0':
        VideoCamera().video.release()
    return HttpResponse(200)
########################UTILS#############################################
def image_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized
