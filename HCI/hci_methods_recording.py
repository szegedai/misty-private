import cv2
from time import gmtime, strftime

recording = False

def default_image_classification_algorithm(image):
    # Write your own method here...
    # At the moment we are just displaying the image
    
    global recording
    # HAMMER Classification Algorithm
    print("Hmm... it looks like a nail!")

    cv2.imshow('VIDEO', image)
    key = cv2.waitKey(1)
    
    # if the spacebar is pressed
    if key%256 == 32:
        img_name = "img_{}.png".format(strftime("%Y%m%d%H%M%S"))
        cv2.imwrite(img_name, image)
        cv2.imshow("1", image)
    
    # if R key is pressed
    if key%256 == 114:
         if recording is False:
            recording = True
         else:
            recording = False

