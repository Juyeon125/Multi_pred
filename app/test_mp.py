import multiprocessing
import time

switch_EC = "Off"
time.sleep(3)
switch_EC = "On"

def DeepEC(seq):
    print("Predict...DeepEC")
    time.sleep(10)
    print("Success Predict DeepEC", seq, "QRS")


def ECPred(seq):
    print("Predict...ECPred")
    time.sleep(4)
    print("Success Predict ECPred", seq, "TUV")


def DETECT(seq):
    print("Predict...DETECT")
    time.sleep(6)
    print("Success Predict DETECT", seq, "WX")


def eCAMI(seq):
    print("Predict...eCAMI")
    time.sleep(8)
    print("Success Predict eCAMI", seq, "YZ")

seq = "ABCDEFGHIJKLMNOP"

if __name__ == '__main__':
    if switch_EC == "On":
        DeepEC = multiprocessing.Process(name='DeepEC', target=DeepEC, args=(seq,))
        ECPred = multiprocessing.Process(name='ECPred', target=ECPred, args=(seq,))
        DETECT = multiprocessing.Process(name='DETECT', target=DETECT, args=(seq,))
        eCAMI = multiprocessing.Process(name='eCAMI', target=eCAMI, args=(seq,))

        DeepEC.start()
        ECPred.start()
        DETECT.start()
        eCAMI.start()