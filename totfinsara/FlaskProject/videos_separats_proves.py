import cv2
import sys
import numpy as np
#from mail import sendEmail
from flask import Flask, render_template, Response, request, send_file
#from flask_basicauth import BasicAuth

import time
import threading
import ifm3dpy
import math
from jinja2 import *
import os
from xml.etree import ElementTree
#per guardar/llegir imatges
import scipy.misc
from PIL import Image
import PIL
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import seaborn as sns
import io


global maxArea, minArea, blobColor, minDistBetweenBlobs, minThreshold, maxThreshold, thresholdStep, minRepeatability, minCircularity, maxCircularity, minConvexity, maxConvexity, minInertiaRatio, maxInertiaRatio
global miarea, maarea, flaggflagg
flaggflagg = False
global frame_inici, frame_inici_amplitut, frame_inici2, frame_inici_amplitut2
global maxAreaValue, minAreaValue, colorBlobValue, minDistBetweenBlobsValue, minThresholdValue, maxThresholdValue, thresholdStepValue, minRepeatabilityValue, minCircularityValue, maxCircularityValue, minConvexityValue, maxConvexityValue, minInertiaRatioValue, maxInertiaRatioValue

global param_flagg
param_flagg = False

global llista, llista_bool
llista = []
llista_bool = False

global static_frame_flagg
static_frame_flagg = False

global frame_escollit, frame_escollit2
global im_xyz, im_rdis, im_amp, amplitut_color

global frame_flagg, frame_flagg2

frame_flagg = 0
frame_flagg2 = 0

global mostra, mostra2

global frame_valid

global calib_flagg
calib_flagg = 0

global headings, headings2
global Punt0, Punt1, Punt2

headings = ("ID","Angle","POS X","POS Y","POS Z")
headings2 = ("ID", "RIGHT","LEFT", "BOTTOM", "TOP", "HEIGHT")

#email_update_interval = 600 # sends an email only once in this time interval
#video_camera = VideoCamera(flip=True) # creates a camera object, flip vertically
#object_classifier = cv2.CascadeClassifier("models/fullbody_recognition_model.xml") # an opencv classifier

# App Globals (do not edit)
app = Flask(__name__)
#run_with_ngrok(app)
#app.config['BASIC_AUTH_USERNAME'] = 'amida4'
#app.config['BASIC_AUTH_PASSWORD'] = 'amida4'
#app.config['BASIC_AUTH_FORCE'] = True

#basic_auth = BasicAuth(app)
last_epoch = 0

fig,ax = plt.subplots(figsize=(6,6))
ax = sns.set_style(style="darkgrid")


@app.route('/visualize')
def visualize():
    global Punt0, Punt1, Punt2

    x=[Punt0[0], Punt1[0], Punt2[0]]
    y=[Punt0[1], Punt1[1], Punt2[1]]

    sns.lineplot(x,y)
    canvas=FigureCanvas(fig)
    img=io.BytesIO()
    fig.savefig(img)
    img.seek(0)
    return send_file(img, mimetype='img/png')


@app.route('/')
#@basic_auth.required

def index():
    return render_template('videos_openCV.html')


def function(flag, cam):
    
    global llista, llista_bool
    global static_frame_flagg, flaggflagg
    global frame_inici, frame_inici_amplitut, frame_inici2, frame_inici_amplitut2
    global miarea, maarea
    global maxAreaValue, minAreaValue, colorBlobValue, minDistBetweenBlobsValue, minThresholdValue, maxThresholdValue, thresholdStepValue, minRepeatabilityValue, minCircularityValue, maxCircularityValue, minConvexityValue, maxConvexityValue, minInertiaRatioValue, maxInertiaRatioValue
    global frame_valid, detector
    global llistaCentreMases,resta_color, img_grey, img_contorns, binary, keyp
    global im_xyz, im_rdis, im_amp
    global amplitut_color_lineas
    
    calib_flagg = 0

    
    grados_flagg = False
    done = False
    reload = False
    contador = 0
    llista = []
    
    ##-- Agafem la informació del background que tenim --##
    ##------- actualment(ho indica frame_flagg) ---------##

    if frame_flagg == 0:
        background_static(1,0)

    if frame_flagg2 == 0:
        background_static2(1,0)


    ##-----Funcio que llegeix els parametres del XML-----##
    
    carreguemValorsXML()
    
    ##---------Assignem el valors llegits al XML---------##        
    
    fg = ifm3dpy.FrameGrabber(cam, ifm3dpy.IMG_AMP | ifm3dpy.IMG_RDIS | ifm3dpy.IMG_CART)
    im = ifm3dpy.ImageBuffer()

    params = cv2.SimpleBlobDetector_Params()

    params.filterByArea = True    # default: True
    params.minArea = int(minAreaValue)          # default: 50
    params.maxArea = int(maxAreaValue)        # default: 5000

    params.filterByCircularity = False      # default: False
    params.minCircularity = float(minCircularityValue)  # default: 0.8
    params.maxCircularity = float(maxCircularityValue)  # default: inf   

    params.filterByConvexity = False       # default: True
    params.minConvexity = float(minConvexityValue)               # default: 0.95
    params.maxConvexity = float(maxConvexityValue)                 # default: Inf

    params.filterByInertia = False        # default: True
    params.minInertiaRatio = float(minInertiaRatioValue)              # default: 0.1
    params.maxInertiaRatio = float(maxInertiaRatioValue)           # default: Inf

    params.minRepeatability = 1           # default: 2

    params.minDistBetweenBlobs = int(minDistBetweenBlobsValue)       # default: 10

    params.thresholdStep = int(thresholdStepValue)            # default: 10
    params.minThreshold = int(minThresholdValue)              # default: 50
    params.maxThreshold = int(maxThresholdValue)              # default: 220


    params.filterByColor = False            # default: True
    params.blobColor = int(colorBlobValue)                    # default: 0

    
    ##-------------Creem blob detector amb------------ ##
    ##----------- els valors dels parametres-----------## 

    detector = cv2.SimpleBlobDetector_create(parameters=params)

    img_blanca = 255 * np.ones((172,224,3), dtype=np.uint8)
    
    llista = []
    
    while not done:

    ##-------- Ens mantenim constantment observant -------##
    ##------- si canviem el valor d'algun parametre ------##

        if param_flagg == True:
            
            if minArea != False:
                params.minArea = int(minArea)
                #print ("minArea:",minArea)
                reload = True
            if maxArea != False:
                params.maxArea = int(maxArea)
                #print ("maxArea:",maxArea)
                reload = True
            if blobColor != False:
                params.blobColor = int(blobColor)
                #print ("blobColor:",blobColor)
                reload = True
            if minDistBetweenBlobs != False:
                params.minDistBetweenBlobs = int(minDistBetweenBlobs)
                #print ("minDistBetweenBlobs:", minDistBetweenBlobs)
                reload = True
            if minThreshold != False:
                params.minThreshold = int(minThreshold)
                #print ("minThreshold:", minThreshold)
                reload = True
            if minRepeatability != False:
                params.minRepeatability = int(minRepeatability)
                #print ("maxThreshold:", maxThreshold)
                reload = True
            if minCircularity != False:
                params.minCircularity = float(minCircularity)
                #print ("thresholdStep:", thresholdStep)
                reload = True
            if maxCircularity != False:
                params.maxCircularity = float(maxCircularity)
                #print ("thresholdStep:", thresholdStep)
                reload = True
            if minConvexity != False:
                params.minConvexity = float(minConvexity)
                #print ("thresholdStep:", thresholdStep)
                reload = True
            if maxConvexity != False:
                params.maxConvexity = float(maxConvexity)
                #print ("thresholdStep:", thresholdStep)
                reload = True
            if minInertiaRatio != False:
                params.minInertiaRatio = float(minInertiaRatio)
                #print ("thresholdStep:", thresholdStep)
                reload = True
            if maxInertiaRatio != False:
                params.maxInertiaRatio = float(maxInertiaRatio)
                #print ("thresholdStep:", thresholdStep)
                reload = True
            

        key = cv2.waitKey(1)

    ##----- Si hem canviat el valor d'algun parametre ----##
    ##------ actualitzem el codi amb els nous valors -----##

        if reload == True: # reload parameters
            del detector
            detector = cv2.SimpleBlobDetector_create(parameters=params)
            #print ("-SimpleBlobDetector_Updated ")
            reload = False
        
        
        ##-------- Capturem els frames i guardem --------##
        ##-----els tipus d'iformacio que necessitem -----##
        
        fg.wait_for_frame(im)

        ##-------- Frame Pixel/Distancia --------##
        im_rdis = im.distance_image()
        ##--------- Frame Pixel/Amplitut --------##
        im_amp = im.amplitude_image()
        ##--------- Frame Pixel/Posicio XYZ --------##
        im_xyz = im.xyz_image()
        

        amplitut_color = cv2.applyColorMap(im_amp.astype(np.uint8), cv2.COLORMAP_BONE)

        resta = frame_inici - im_rdis
        resta2 = frame_inici2 - im_rdis

        resta_altura =  resta


        acum1 = 0
        acum2 = 0
        
        for i in range(171):
            for j in range(223):
                
                acum1 += resta[i][j]
                acum2 += resta2[i][j]

                if resta[i][j] > 0.01:
                    resta[i][j]= 0    #blanc
                else:
                    resta[i][j]= 100  #negre

                if resta_altura[i][j] > 0.01:
                    resta_altura[i][j]= 0   #blanc
                else:
                    resta_altura[i][j]= 100


        
    ##-----Escollim dinàmicament en cada iteracio-------##
    ##--Si ens quedem amb el background1 o background2--##
        
        ##--Background2 valid--##
        
        if abs(acum1) > abs(acum2):
            frame_valid = 1
            resta = resta2
        
        ##--Background1 valid--##

        else:
            frame_valid = 2


        calcularInfoResta(resta, amplitut_color, detector)
        calcularInfoRestaAltura(resta_altura, amplitut_color, detector, llistaCentreMases, im_xyz)

        amplitut_color[86, 112] = [0, 0, 255]

        amplitut_color_lineas = amplitut_color
        

        if flag == 1:
            if len(llistaCentreMases) == 3:
            #e1 = im_xyz[int(llistaCentreMases[0][1]),int(llistaCentreMases[0][0]),0] 
            #e2 = im_xyz[int(llistaCentreMases[1][1]),int(llistaCentreMases[1][0]),0] 
            #e3 = im_xyz[int(llistaCentreMases[2][1]),int(llistaCentreMases[2][0]),0] 
            #print(e1,e2,e3)

                cv2.line(amplitut_color_lineas,(int(llistaCentreMases[0][0]),int(llistaCentreMases[0][1])),(int(llistaCentreMases[1][0]),int(llistaCentreMases[1][1])),(0,255,0), 1)
                cv2.line(amplitut_color_lineas,(int(llistaCentreMases[0][0]),int(llistaCentreMases[0][1])),(int(llistaCentreMases[2][0]),int(llistaCentreMases[2][1])),(0,255,0), 1)
                cv2.line(amplitut_color_lineas,(int(llistaCentreMases[2][0]),int(llistaCentreMases[2][1])),(int(llistaCentreMases[1][0]),int(llistaCentreMases[1][1])),(0,255,0), 1)

                scipy.misc.imsave('static/img/calibracio.jpg', amplitut_color_lineas)

            ret, jpeg = cv2.imencode('.jpg',amplitut_color_lineas)
        
        elif flag == 2:
            ret, jpeg = cv2.imencode('.jpg',amplitut_color)
        elif flag == 3:
            ret, jpeg = cv2.imencode('.jpg',resta_color)
        elif flag == 4:
            ret, jpeg = cv2.imencode('.jpg',img_grey)
        elif flag == 5:
            ret, jpeg = cv2.imencode('.jpg',binary)
        elif flag == 6:
            ret, jpeg = cv2.imencode('.jpg',img_contorns)
        elif flag == 7:
            ret, jpeg = cv2.imencode('.jpg',keyp)
        elif flag == 8:
            ret, jpeg = cv2.imencode('.jpg',resta_altura)
            
        
        if jpeg is not None:

            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        else:
            print("frame is none")
        
@app.route('/calibrate')
def calibrate():
    global calib_flagg
    global im_xyz, im_rdis, im_amp, frame_inici, detector, img_contorns, amplitut_color
    
    amplitut_color = cv2.applyColorMap(im_amp.astype(np.uint8), cv2.COLORMAP_BONE)
    resta_C = frame_inici - im_rdis
    
    for i in range(171):
        for j in range(223):

            if resta_C[i][j] > 0.04:
                resta_C[i][j]= 0    #blanc
            else:
                resta_C[i][j]= 100  #negre

 
    calibratge(resta_C, detector)
    
    if calib_flagg != 0:
        return render_template("error_calibracio.html", calib_flagg = calib_flagg)
    else:
        return render_template("resultats_calibracio.html")

@app.route('/1')
def video1():
    return Response(function(1, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/2')
def video2():
    return Response(function(2, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/3')
def video3():
    return Response(function(3, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')
    
@app.route('/4')
def video4():
    return Response(function(4, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/5')
def video5():
    return Response(function(5, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/6')
def video6():
    return Response(function(6, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/7')
def video7():
    return Response(function(7, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/8')
def video8():
    return Response(function(8, ifm3dpy.Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')
  
@app.route('/video1')
def vid1():
    return render_template("videos_openCV.html", a = 1)

@app.route('/video2')
def vid2():
    return render_template("videos_openCV.html", a = 2)

@app.route('/video3')
def vid3():
    return render_template("videos_openCV.html", a = 3)

@app.route('/video4')
def vid4():
    return render_template("videos_openCV.html", a = 4)

@app.route('/video5')
def vid5():
    return render_template("videos_openCV.html", a = 5)

@app.route('/video6')
def vid6():
    return render_template("videos_openCV.html", a = 6)

@app.route('/video8')
def vid8():
    return render_template("videos_openCV.html", a = 8)


@app.route("/parametres", methods=["POST", "GET"])
def params():
    global maxArea, minArea, blobColor, minDistBetweenBlobs, minThreshold, maxThreshold, thresholdStep, minRepeatability, minCircularity, maxCircularity, minConvexity, maxConvexity, minInertiaRatio, maxInertiaRatio 
    global maxAreaValue, minAreaValue, colorBlobValue, minDistBetweenBlobsValue, minThresholdValue, maxThresholdValue, thresholdStepValue, minRepeatabilityValue, minCircularityValue, maxCircularityValue, minConvexityValue, maxConvexityValue, minInertiaRatioValue, maxInertiaRatioValue
    
    global param_flagg, flaggflagg
    function(7,ifm3dpy.Camera())

    
    if request.method == "POST":
        

        #flag_lectura = False
        flaggflagg = True
        minArea = request.form["minArea"]
        maxArea = request.form["maxArea"]
        blobColor = request.form["blobColor"]
        minDistBetweenBlobs = request.form["minDistBetweenBlobs"]
        minThreshold = request.form["minThreshold"]
        maxThreshold = request.form["maxThreshold"]
        thresholdStep = request.form["thresholdStep"]
        minRepeatability = request.form["minRepeatability"]
        minCircularity = request.form["minCircularity"]
        maxCircularity = request.form["maxCircularity"]
        minConvexity = request.form["minConvexity"]
        maxConvexity = request.form["maxConvexity"]
        minInertiaRatio = request.form["minInertiaRatio"]
        maxInertiaRatio = request.form["maxInertiaRatio"]


        param_flagg = True


        file_name = 'templates/arxiu.xml'
        dom = ElementTree.parse(file_name)
        parametres = dom.findall('Parametres')
        root = dom.getroot()
        
   
        for minarea in root.iter("minArea"):
            minarea.text= minArea
        for maxarea in root.iter("maxArea"):
            maxarea.text= maxArea
        for blobcolor in root.iter("colorBlob"):
            blobcolor.text= blobColor
        for mindist in root.iter("minDistBetweenBlobs"):
            mindist.text= minDistBetweenBlobs
        for minthres in root.iter("minThreshold"):
            minthres.text= minThreshold
        for maxthres in root.iter("maxThreshold"):
            maxthres.text= maxThreshold
        for thresstep in root.iter("thresholdStep"):
            thresstep.text= thresholdStep
        for mirep in root.iter("minRepeatability"):
            mirep.text= minRepeatability
        for micirc in root.iter("minCircularity"):
            micirc.text= minCircularity
        for macirc in root.iter("maxCircularity"):
            macirc.text= maxCircularity
        for miconv in root.iter("minConvexity"):
            miconv.text= minConvexity
        for maconv in root.iter("maxConvexity"):
            maconv.text= maxConvexity
        for miinert in root.iter("minInertiaRatio"):
            miinert.text= minInertiaRatio
        for mainert in root.iter("maxInertiaRatio"):
            mainert.text= maxInertiaRatio

        with open(file_name,"wb") as fileupdate:
            dom.write(fileupdate)


        return render_template("parametres.html", param_flagg = param_flagg, minAreaResp = minArea, maxAreaResp = maxArea, blobColorResp = blobColor, minDistResp = minDistBetweenBlobs, minThresholdResp = minThreshold, maxThresholdResp = maxThreshold, thresholdStepResp = thresholdStep, minRepeatabilityResp = minRepeatability , minCircularityResp = minCircularity, maxCircularityResp = maxCircularity, minConvexityResp = minConvexity, maxConvexityResp = maxConvexity, minInertiaRatioResp = minInertiaRatio, maxInertiaRatioResp = maxInertiaRatio)
    
    else:

        #if flaggflagg == True:
        return render_template("parametres.html",  minAreaR = minAreaValue, maxAreaR = maxAreaValue, colorBlobR = colorBlobValue, minDistR = minDistBetweenBlobsValue, minThresholdR = minThresholdValue, maxThresholdR = maxThresholdValue, thresholdStepR = thresholdStepValue, minRepeatabilityR = minRepeatabilityValue, minCircularityR = minCircularityValue, maxCircularityR = maxCircularityValue, minConvexityR = minConvexityValue, maxConvexityR = maxConvexityValue, minInertiaRatioR = minInertiaRatioValue, maxInertiaRatioR = maxInertiaRatioValue)



@app.route("/angles", methods=["POST", "GET"])
def angles():
    global llista_bool

    return render_template("angles.html", llista_bool = llista_bool, llista_definitiva = llista_definitiva, headings = headings, headings2 = headings2, llista_definitiva2 = llista_definitiva2)


@app.route("/configuracio", methods=["POST", "GET"])
def staticFrame():
    global frame_flagg, frame_flagg2, frame_valid

    return render_template("configuracio.html", frame_valid = frame_valid)


@app.route('/20')
def background1():
    
    return Response(background_static(1,0), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/21')
def background1_choosed():

    return Response(background_static(2,0), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/22')
def background2():
    return Response(background_static2(1,0), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/23')
def background2_choosed():
    global mostra2
    mostra2 = True
    return Response(background_static2(2,0), mimetype='multipart/x-mixed-replace; boundary=frame' )


def background_static(v, cam):
    global frame_inici, frame_inici_amplitut,frame_escollit
    
    if v == 2:
        
        image = cv2.imread(frame_escollit, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        image_ok = cv2.resize(image, (224,172))
        
        #frame_inici = matriu
        #frame_inici_amplitut = frame_escollit

        ret, jpeg = cv2.imencode('.jpg',image_ok)
        if jpeg is not None:
            
            return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    
    elif v == 1:
        image = cv2.imread('background1.png', cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        image_ok = cv2.resize(image, (224,172))
        matriu = np.load('background1.dat', allow_pickle=True)
        
        frame_escollit = 'background1.png'
        frame_inici = matriu
        frame_inici_amplitut = image_ok

        ret, jpeg = cv2.imencode('.jpg',image_ok)
        if jpeg is not None:
            
            return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    
    elif v == 3:

        fg = ifm3dpy.FrameGrabber(cam, ifm3dpy.IMG_AMP | ifm3dpy.IMG_RDIS | ifm3dpy.IMG_CART)
        im = ifm3dpy.ImageBuffer()
        fg.wait_for_frame(im)

        frame_inici_amplitut = im.amplitude_image()

        frame_inici = im.distance_image()
        frame_inici.dump('AMIDA4.dat')

        #frame_inici.dump('frameEscollit1.dat')
        #guardamos imagen con nombre
        #im = Image.fromarray(frame_inici_amplitut)
        scipy.misc.imsave('AMIDA4.jpg', frame_inici_amplitut)
        frame_escollit = 'AMIDA4.jpg'
        

        #ret, jpeg = cv2.imencode('.jpg',frame_escollit)
        #if jpeg is not None:
            
        #    return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        
    else:
        pass

def background_static2(v, cam):

    global frame_inici2, frame_inici_amplitut2, frame_escollit2, mostra2

    if v == 2:
        
        image = cv2.imread(frame_escollit2, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        image_ok = cv2.resize(image, (224,172))
        
        
        ret, jpeg = cv2.imencode('.jpg',image_ok)
        if jpeg is not None:
            
            return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    elif v == 1:
        image = cv2.imread('background2.png', cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        image_ok = cv2.resize(image, (224,172))
        matriu2 = np.load('background2.dat', allow_pickle=True)
        
        frame_escollit2 = 'background2.png'

        frame_inici2 = matriu2
        frame_inici_amplitut2 = image_ok

        ret, jpeg = cv2.imencode('.jpg',image_ok)
        if jpeg is not None:
            
            return (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
 
    elif v == 3:
        
        fg = ifm3dpy.FrameGrabber(cam, ifm3dpy.IMG_AMP | ifm3dpy.IMG_RDIS | ifm3dpy.IMG_CART)
        im = ifm3dpy.ImageBuffer()
        fg.wait_for_frame(im)

        frame_inici_amplitut2 = im.amplitude_image()

        frame_inici2 = im.distance_image()
        frame_inici2.dump('AMIDA4_2.dat')

        scipy.misc.imsave('AMIDA4_2.jpg', frame_inici_amplitut2)
        frame_escollit2 = 'AMIDA4_2.jpg'
    else:
        pass


#@app.route("/llegirXML", methods=["POST"])
#def llegirXML():

#    file_name = 'templates/arxiu.xml'
    #full_file = os.path.abspath(os.path.join(file_name))
#    dom = ElementTree.parse(file_name)
#    parametres = dom.findall('EventItem')

#    if request.method == 'POST':
#        for p in parametres:
#            flag_lectura = True
#            minArea = p.find('minArea').text
#            maxArea = p.find('maxArea').text
#            colorBlob = p.find('colorBlob').text
#            minDistBetweenBlobs = p.find('minDistBetweenBlobs').text
#            minThreshold = p.find('minThreshold').text
#            maxThreshold = p.find('maxThreshold').text
#            thresholdStep = p.find('thresholdStep').text

#        return render_template("parametres.html", flag= flag_lectura, minAreaR = minArea, maxAreaR = maxArea, colorBlobR = colorBlob, minDistR = minDistBetweenBlobs, minThresholdR = minThreshold, maxThresholdR = maxThreshold, thresholdStepR = thresholdStep)
#    else:
#        return render_template("parametres.html")



@app.route("/enviarFrame", methods=["POST"])
def enviarFrame():
    global frame_inici, frame_inici_amplitut, frame_flagg, frame_flagg2, frame_escollit
    
    frame_flagg += 1 

    if request.method == 'POST':
        
        frame_escollit = request.form["nom_frame"]
        
        if frame_escollit.endswith('.png') or frame_escollit.endswith('.jpg'):
            frame_escollit_retallat = frame_escollit[:-4]
            frame_dat = frame_escollit_retallat + '.dat'
        
        
        frame_inici = np.load(frame_dat, allow_pickle=True)
        
        background_static(2,0)
        return render_template("frame.html", frame_flagg = frame_flagg, frame_flagg2 = frame_flagg2)
    
    return render_template("frame.html", frame_flagg = frame_flagg, frame_flagg2 = frame_flagg2)
    
@app.route("/enviarFrame2", methods=["POST"])
def enviarFrame2():
    global frame_inici2, frame_inici_amplitut2, frame_flagg2, frame_escollit2
    
    frame_flagg2 += 1 
    
    if request.method == 'POST':
        
        frame_escollit2 = request.form["nom_frame2"]
        if frame_escollit2.endswith('.png') or frame_escollit2.endswith('.jpg'):
            frame_escollit2_retallat = frame_escollit2[:-4]
            frame_dat2 = frame_escollit2_retallat + '.dat'

        frame_inici2 = np.load(frame_dat2, allow_pickle=True)
        
        background_static2(2,0)

        return render_template("frame.html", frame_flagg2 = frame_flagg2)
    
    return render_template("frame.html", frame_flagg2 = frame_flagg2)

@app.route("/treureFrame1")
def treureFrame1():  
    global frame_flagg, frame_flagg2
    frame_flagg = 1
    
    background_static(3, ifm3dpy.Camera())
    return render_template("/frame.html", frame_flagg = frame_flagg, frame_flagg2 = frame_flagg2)
     


@app.route("/treureFrame2")
def treureFrame2(): 
    global frame_flagg, frame_flagg2
    
    frame_flagg2 = 1

    background_static2(3, ifm3dpy.Camera())
    return render_template("/frame.html")


@app.route("/guardarFrame")
def guardarFrame():  
    global frame_inici, frame_inici_amplitut
    
    frame_inici.dump('background1.dat')
    scipy.misc.imsave('background1.png', frame_inici_amplitut)
    background_static(1,0)
    return render_template("/frame.html")
    


@app.route("/guardarFrame2")
def guardarFrame2(): 
    global frame_inici2, frame_inici_amplitut2
    
    frame_inici2.dump('background2.dat')
    scipy.misc.imsave('background2.png', frame_inici_amplitut2)
    background_static2(1,0)
    return render_template("/frame.html")



##---------------FUNCIONS NO FLASK-------------------##
##---------------FUNCIONS NO FLASK-------------------##
##---------------FUNCIONS NO FLASK-------------------##
##---------------FUNCIONS NO FLASK-------------------##
##---------------FUNCIONS NO FLASK-------------------##


def carreguemValorsXML():

    global maxAreaValue, minAreaValue, colorBlobValue, minDistBetweenBlobsValue, minThresholdValue, maxThresholdValue, thresholdStepValue, minRepeatabilityValue, minCircularityValue, maxCircularityValue, minConvexityValue, maxConvexityValue, minInertiaRatioValue, maxInertiaRatioValue

    file_name = 'templates/arxiu.xml'
    dom = ElementTree.parse(file_name)
    parametres = dom.findall('Parametres')
    root = dom.getroot()
    
    for p in parametres:
        
        minAreaValue = p.find('minArea').text
        maxAreaValue = p.find('maxArea').text
        colorBlobValue = p.find('colorBlob').text
        minDistBetweenBlobsValue = p.find('minDistBetweenBlobs').text
        minThresholdValue = p.find('minThreshold').text
        maxThresholdValue = p.find('maxThreshold').text
        thresholdStepValue = p.find('thresholdStep').text
        minRepeatabilityValue = p.find('minRepeatability').text
        minCircularityValue = p.find('minCircularity').text
        maxCircularityValue = p.find('maxCircularity').text
        minConvexityValue = p.find('minConvexity').text
        maxConvexityValue = p.find('maxConvexity').text
        minInertiaRatioValue = p.find('minInertiaRatio').text
        maxInertiaRatioValue = p.find('maxInertiaRatio').text


def calcularInfoResta(resta, amplitut_color, detector):
    
    global llistaCentreMases,resta_color, img_grey, img_contorns, binary, keyp
    global llista_bool, llista_definitiva, llista_definitiva2
    matriu_blanc = np.zeros((172,224), np.uint8)
    resta_color = cv2.applyColorMap(resta.astype(np.uint8), cv2.COLORMAP_TWILIGHT)
    img_grey = cv2.cvtColor(resta_color, cv2.COLOR_BGR2GRAY)
    keypoints = detector.detect(img_grey)
    _, binary = cv2.threshold(img_grey, 100,255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    img_contorns = cv2.drawContours(matriu_blanc, contours, -1 ,(255,0,0), 1)

    llistaCentreMases = []
    llista_definitiva = [0,0,0,0,0,0]
    llista_definitiva2 = [0,0,0,0,0,0]
    
    if len(keypoints) > 0:
        
        for k in range(len(keypoints)):
            #print(len(keypoints))
            llista = []
            llista2 = []
            sumatori = 0
            
            x = keypoints[k].pt[0]
            y = keypoints[k].pt[1]
            
            cv2.putText(amplitut_color,str(k),(int(x),int(y)),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255),1)
            for cnt in contours:
                
                area = cv2.contourArea(cnt)
                
                if area > 100 and area < 1200:   
                    
                    M = cv2.moments(cnt)
                    
                    if M['m00'] != 0:
                        
                        
                        #centroid
                        X = M['m10'] / M['m00']
                        Y = M['m01'] / M['m00']
                        
                        if [X,Y] not in llistaCentreMases:
                            
                            llistaCentreMases.append([X,Y])
                             
                    if M['mu20']-M['mu02'] != 0:
                        
                        grados_flagg = True
                        
                        theta = 0.5 * np.arctan (2 * M['mu11']/((M['mu20']-M['mu02'])))
                        grados = (theta / math.pi) * 180
                        grados = round(grados, 2)
                        
                        if grados < 0:
                            grados = 45 + (45 - abs(grados))
                        
                        
                        llista_definitiva[sumatori] = [sumatori, grados]
                        llista_definitiva2[sumatori] = [sumatori] 

                        llista_bool = True
                        sumatori += 1
  
    

    #print(llistaCentreMases)      
    keyp = cv2.drawKeypoints(amplitut_color,keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    


def calcularInfoRestaAltura(resta_altura, amplitut_color, detector, llistaCentreMases, im_xyz):
    
    global llista_definitiva ,llista_definitiva2, mitjanaReal, ite
    
    matriu_blanc = np.zeros((172,224), np.uint8)
    resta_altura = cv2.applyColorMap(resta_altura.astype(np.uint8), cv2.COLORMAP_TWILIGHT)
    img_grey_rest = cv2.cvtColor(resta_altura, cv2.COLOR_BGR2GRAY)
    keypoints_rest = detector.detect(img_grey_rest)
    _, binary_rest = cv2.threshold(img_grey_rest, 100,255, cv2.THRESH_BINARY)
    contours_rest, _ = cv2.findContours(binary_rest, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    img_contorns_rest = cv2.drawContours(matriu_blanc, contours_rest, -1 ,(255,0,0), 1)
  
    llista_cnt = []
    iteracions = 0
    ite = len(llistaCentreMases)
    
    if ite > 0:    
        #for k in range(len(llistaCentreMases)):
        mitjanaReal = [0 for i in range (ite)]
        #mitjanaReal =[0,0,0,0,0]   
        for cnt in contours_rest:
            x_sum = 0
            y_sum = 0
            z_sum = 0

            contador = 0
            area_rest = cv2.contourArea(cnt)
            
            if area_rest > 200 and area_rest < 1200:
            
                max_left = -10
                max_right = 10
                max_top = -10
                max_bottom = 10
                max_height = 10

                for y in range(0,171):
                    for x in range(0,223):
                        
                        dist = cv2.pointPolygonTest(cnt, (x,y), True)
                        if dist >= 0:
                            if im_xyz[y,x,1] > max_left:
                                max_left = round(im_xyz[y,x,1],4)
                            if im_xyz[y,x,1] < max_right:
                                max_right = round(im_xyz[y,x,1],4)
                            
                            if im_xyz[y,x,2] > max_top:
                                max_top = round(im_xyz[y,x,2],4)
                            if im_xyz[y,x,2] < max_bottom:
                                max_bottom = round(im_xyz[y,x,2],4)
                            
                            if im_xyz[y,x,0] < max_height:    
                                max_height = round(im_xyz[y,x,0],4)
                            
                            x_sum += im_xyz[y,x, 1] 
                            y_sum += im_xyz[y,x, 2] 
                            z_sum += im_xyz[y,x, 0] 

                            contador += 1


                #for cont in cnt:
                #    x_sum += im_xyz[cnt[contador][0][1],cnt[contador][0][0], 1] 
                #    y_sum += im_xyz[cnt[contador][0][1],cnt[contador][0][0], 2] 
                #    z_sum += im_xyz[cnt[contador][0][1],cnt[contador][0][0], 0] 
                    
                #    contador += 1
                
                if contador != 0:
                    
                    RealPointX = round(x_sum/contador, 4)
                    RealPointY = round(y_sum/contador, 4)
                    RealPointZ = round(z_sum/contador, 4)

                    #print(RealPointX, RealPointY, RealPointZ)

                    mitjanaReal[iteracions] = RealPointX, RealPointY, RealPointZ         
                   
                    llista_definitiva[iteracions].append(RealPointX)
                    llista_definitiva[iteracions].append(RealPointY)
                    llista_definitiva[iteracions].append(RealPointZ)

                    llista_definitiva2[iteracions].append(max_left)
                    llista_definitiva2[iteracions].append(max_right)
                    llista_definitiva2[iteracions].append(max_top)
                    llista_definitiva2[iteracions].append(max_bottom)
                    llista_definitiva2[iteracions].append(max_height)

                    iteracions += 1
                    
    #if len(llistaCentreMases) > 0:
        #print(llista_definitiva)
        #print(mitjanaReal)


def calibratge(resta,detector):
    
    global amplitut_color, llistaCentreMases
    global llista_bool, llista_definitiva, llista_definitiva2, mitjanaReal
    global calib_flagg
    global Punt0, Punt1, Punt2

    matriu_blanc = np.zeros((172,224), np.uint8)
    resta_color = cv2.applyColorMap(resta.astype(np.uint8), cv2.COLORMAP_TWILIGHT)
    img_grey = cv2.cvtColor(resta_color, cv2.COLOR_BGR2GRAY)
    keypoints_C = detector.detect(img_grey)
    _, binary = cv2.threshold(img_grey, 100,255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    img_contorns = cv2.drawContours(matriu_blanc, contours, -1 ,(255,0,0), 1)

    llistaCentreMases_C = []
    print(len(keypoints_C))
    num_elements = 0
    if len(llistaCentreMases) > 0:

        for k in range(len(llistaCentreMases)):
            #print(len(keypoints))
            llista = []
            llista2 = []
  
            num_elements += 1
            
            #x = keypoints_C[k].pt[0]
            #y = keypoints_C[k].pt[1]
            
            #cv2.putText(amplitut_color,str(k),(int(x),int(y)),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255),1)
            
            for cnt in contours:
                
                area = cv2.contourArea(cnt)
                
                if area > 100 and area < 1200:   
                    
                    M = cv2.moments(cnt)
                    
                    if M['m00'] != 0:
                        
                        #centroid
                        X = M['m10'] / M['m00']
                        Y = M['m01'] / M['m00']
                        
                        if [X,Y] not in llistaCentreMases_C:
                            
                            llistaCentreMases_C.append([X,Y])

                        llista_bool = True
                       
    print(llistaCentreMases_C)      
    keyp = cv2.drawKeypoints(amplitut_color,keypoints_C, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    
    if num_elements == 3:
        print("Els tres elements han sigut detectats correctament")
        calcularInfoRestaAltura(resta, amplitut_color, detector, llistaCentreMases, im_xyz)
        
        P0 = llistaCentreMases[0]
        P1 = llistaCentreMases[1]
        P2 = llistaCentreMases[2]

        P0_X = im_xyz[int(llistaCentreMases[0][1]),int(llistaCentreMases[0][0]),1]
        P0_Y = im_xyz[int(llistaCentreMases[0][1]),int(llistaCentreMases[0][0]),2]
        P0_Z = im_xyz[int(llistaCentreMases[0][1]),int(llistaCentreMases[0][0]),0]
        
        P1_X = im_xyz[int(llistaCentreMases[1][1]),int(llistaCentreMases[1][0]),1]
        P1_Y = im_xyz[int(llistaCentreMases[1][1]),int(llistaCentreMases[1][0]),2]
        P1_Z = im_xyz[int(llistaCentreMases[1][1]),int(llistaCentreMases[1][0]),0]
        
        P2_X = im_xyz[int(llistaCentreMases[2][1]),int(llistaCentreMases[2][0]),1]
        P2_Y = im_xyz[int(llistaCentreMases[2][1]),int(llistaCentreMases[2][0]),2]
        P2_Z = im_xyz[int(llistaCentreMases[2][1]),int(llistaCentreMases[2][0]),0]
        
        print(P0_X,P0_Y,P0_Z)
        print(P1_X,P1_Y,P1_Z)
        print(P2_X,P2_Y,P2_Z)


        distancia1 = math.sqrt(((P1_X-P0_X)**2)+((P1_Y-P0_Y)**2))
        distancia2 = math.sqrt(((P1_X-P2_X)**2)+((P1_Y-P2_Y)**2))
        distancia3 = math.sqrt(((P0_X-P2_X)**2)+((P0_Y-P2_Y)**2))
        
        #print(distancia1,distancia2,distancia3)
    
        if distancia1 > distancia2 and distancia1 > distancia3:
            Punt0 = [P2_X, P2_Y, P2_Z]
            if distancia2 > distancia3:
                Punt1 = [P1_X, P1_Y, P1_Z]
                Punt2 = [P0_X, P0_Y, P0_Z]
            else:
                Punt1 = [P0_X, P0_Y, P0_Z]
                Punt2 = [P1_X, P1_Y, P1_Z]

        elif distancia2 > distancia1 and distancia2 > distancia3:
            Punt0 = [P0_X, P0_Y, P0_Z]
            if distancia1 > distancia3:
                Punt1 = [P1_X, P1_Y, P1_Z]
                Punt2 = [P0_X, P0_Y, P0_Z]
            else:
                Punt1 = [P0_X, P0_Y, P0_Z]
                Punt2 = [P1_X, P1_Y, P1_Z]
            
        elif distancia3 > distancia1 and distancia3 > distancia2:
            Punt0 = [P1_X, P1_Y, P1_Z]
            if distancia1 > distancia2:
                Punt1 = [P0_X, P0_Y, P0_Z]
                Punt2 = [P2_X, P2_Y, P2_Z]
            else:
                Punt1 = [P2_X, P2_Y, P2_Z]
                Punt2 = [P0_X, P0_Y, P0_Z]
        
        #print(Punt0)

        print(P0_Z, P1_Z, P2_Z)
        if abs(P0_Z - P1_Z) > 0.01:
            print("Error: L'alçada dels objectes no es vàlida")
            calib_flagg = 4
            
        if abs(P1_Z - P2_Z) > 0.01:
            print("Error: L'alçada dels objectes no es vàlida")
            calib_flagg = 4
        
        if abs(P2_Z - P0_Z) > 0.01:
            print("Error: L'alçada dels objectes no es vàlida")
            calib_flagg = 4
       
        angle_rad = math.atan2((Punt0[0]-Punt1[0]),(Punt0[1]-Punt1[1]))
        angle_rad2 = math.atan2((Punt1[0]-Punt0[0]),(Punt1[1]-Punt0[1]))

        angle_graus = (angle_rad * 180)/ math.pi
        angle_graus2 = (angle_rad2 * 180)/ math.pi

        print(angle_graus, angle_graus2)
        suma_graus = abs(angle_graus) + abs(angle_graus2)
        if suma_graus != 180:
            calib_flagg = 5

        #angle_graus2 = (angle_rad2 * 180)/ math.pi

        #print(angle_graus, angle_graus2)

        #desplaçament = Punt0[0],Punt0[1] 
        #print(desplaçament)

    elif num_elements == 2:
        calib_flagg = 1
        print("Error: Falta detectar 1 element per poder calibrar")  
    
    elif num_elements == 1:
        calib_flagg = 2
        print("Error: Falten detectar 2 elements per poder calibrar")

    elif num_elements == 0:
        calib_flagg = 3
        print("Error: Falten detectar 3 elements per poder calibrar")

    
if __name__ == '__main__':
    app.run(host='192.168.0.80', debug=True, threaded=True)