# -*- coding: utf-8 -*-
"""
Created on Sun Feb 22 13:35:51 2026

@author: Valerie
@contributions: Matthias - reformatted and added functionality for UI linkage via api.py file
"""

import os
import cv2
import shutil
import numpy as np
from ultralytics import YOLO
from datetime import datetime


# Globals used by your existing functions
img_tb = None
result_TB = None
boxes = None

# In-memory crops (replace file counters)
CP_CROPS, FM_CROPS, FU_CROPS, HS_CROPS = [], [], [], []

# Tool statuses (set by defect functions)
CP_STATUS = "missing"
FM_STATUS = "missing"
FU_STATUS = "missing"
HS_STATUS = "missing"

# Report returned to API
REPORT = {"overall": "", "tools": []}

# New: run/session id + outputs directory + annotated images for API
RUN_ID = None
OUT_DIR = "outputs"
_IMAGES = {}   # {"toolbox": bgr, "Chop Phaco": bgr, "Forceps Macpherson": bgr, ...}

def Chop_Phaco():
    if 0 not in boxes.cls:
        print("Chop Phaco is missing")
        return True
    return False


def Forceps_Macpherson():
    if 1 not in boxes.cls:
        print("Forceps Macpherson is missing")
        return True
    return False


def Forceps_Utrata():
    if 2 not in boxes.cls:
        print("Forceps Utrata is missing")
        return True
    return False


def Hook_Sinskey():
    if 3 not in boxes.cls:
        print("Hook Sinskey Tip is missing")
        return True
    return False


# count tools in prediction for tool box
def count_tools():
    # sets REPORT["overall"] without extra helpers
    missing = []
    if Chop_Phaco(): missing.append("Chop Phaco")
    if Forceps_Macpherson(): missing.append("Forceps Macpherson")
    if Forceps_Utrata(): missing.append("Forceps Utrata")
    if Hook_Sinskey(): missing.append("Hook Sinskey Tip")

    if len(missing) == 0:
        REPORT["overall"] = "All present"
    else:
        REPORT["overall"] = "Missing: " + ", ".join(missing)


def crop_img():
    if 0 in boxes.cls:
        crop_CP()
    if 1 in boxes.cls:
        crop_FM()
    if 2 in boxes.cls:
        crop_FU()
    if 3 in boxes.cls:
        crop_HS()


def crop_CP():
    global CP_CROPS
    xyxy = boxes.xyxy
    xywh = boxes.xywh
    for i in range(len(boxes.cls)):
        if boxes.cls[i] == 0:
            a_CP = int(xyxy[i][0]+xywh[i][2]+60)
            b_CP = int(xyxy[i][1]+xywh[i][2]+60)
            c_CP = int(xyxy[i][2]-xywh[i][2]-60)
            d_CP = int(xyxy[i][3]-xywh[i][2]-60)
            crop_CP5 = img_tb[int(xyxy[i][1]-60):int(b_CP), int(xyxy[i][0]-60):int(a_CP)]
            crop_CP6 = img_tb[d_CP:int(xyxy[i][3]+60), c_CP:int(xyxy[i][2]+60)]
            kernel = np.array([[0, -1,  0],
                               [-1, 5, -1],
                               [0, -1,  0]])
            crop_CP3 = img_tb[int(xyxy[i][1]):int(xyxy[i][3]), int(xyxy[i][0]):int(xyxy[i][2])]
            # sharpen image
            sharp_CP3 = cv2.filter2D(crop_CP3, -1, kernel)

            CP_CROPS.append(sharp_CP3)

            with open('CP file num.txt', 'r') as f:
                count_CP = int(f.read().strip())
            cv2.imwrite(f"Chop Phaco Tip2/cropped_CP{count_CP}.png", sharp_CP3)
            with open(f'Chop Phaco Tip2/cropped_CP{count_CP}.txt', 'w') as a:
                a.write(f"{int(boxes.cls[i])} {xyxy[i][0]} {xyxy[i][1]} {xyxy[i][2]} {xyxy[i][3]}")
            with open("CP file num.txt", 'w') as f:
                f.write(str(count_CP + 1))
        else:
            i = i + 1
    CP_defect()


def crop_FM():
    global FM_CROPS
    xyxy = boxes.xyxy
    xywh = boxes.xywh
    for i in range(len(boxes.cls)):
        if boxes.cls[i] == 1:
            crop_FM3 = img_tb[int(xyxy[i][1]):int(xyxy[i][3]), int(xyxy[i][0]):int(xyxy[i][2])]
            a_FM = int(xyxy[i][0]+xywh[i][3]+70)
            b_FM = int(xyxy[i][1]+xywh[i][3]+70)
            c_FM = int(xyxy[i][3]-xywh[i][3]-70)
            d_FM = int(xyxy[i][2]-xywh[i][3]-70)
            crop_FM4 = img_tb[int(xyxy[i][1]-70):int(b_FM), int(xyxy[i][0]-70):int(a_FM)]
            crop_FM5 =img_tb[c_FM:int(xyxy[i][3]+70), d_FM:int(xyxy[i][2]+70)]
            kernel = np.array([[0, -1,  0],
                               [-1, 4.8, -1],
                               [0, -1,  0]])
            sharp_FM3 = cv2.filter2D(crop_FM3, -1, kernel)

            FM_CROPS.append(sharp_FM3)

            with open('FM file num.txt', 'r') as g:
                count_FM = int(g.read().strip())
            with open(f'Forceps Macpherson Tip/cropped_FM{count_FM}.txt', 'w') as b:
                b.write(f"{int(boxes.cls[i])} {xyxy[i][0]} {xyxy[i][1]} {xyxy[i][2]} {xyxy[i][3]}")
            # cv2.imshow("new crop3.png",sharp_FM3)
            cv2.imwrite(f"Forceps Macpherson Tip/cropped_FM{count_FM}.png", sharp_FM3)
            with open("FM file num.txt", 'w') as g:
                g.write(str(count_FM + 1))
        else:
            i = i + 1
    FM_defect()


def crop_FU():
    global FU_CROPS
    xyxy = boxes.xyxy
    xywh = boxes.xywh
    for i in range(len(boxes.cls)):
        if boxes.cls[i] == 2:
            crop_FU3 = img_tb[int(xyxy[i][1]):int(xyxy[i][3]), int(xyxy[i][0]):int(xyxy[i][2])]
            a_FU = int(xyxy[i][0]+xywh[i][3]+80)
            b_FU = int(xyxy[i][1]+xywh[i][3]+80)
            c_FU = int(xyxy[i][3]-xywh[i][3]-70)
            d_FU = int(xyxy[i][2]-xywh[i][3]-70)
            crop_FU4 = img_tb[int(xyxy[i][1]-80):int(b_FU), int(xyxy[i][0]-80):int(a_FU)]
            crop_FU5 =img_tb[c_FU:int(xyxy[i][3]+70), d_FU:int(xyxy[i][2]+70)]
            kernel = np.array([[0, -1,  0],
                               [-1,  5.2, -1],
                               [0, -1,  0]])
            sharp_FU3 = cv2.filter2D(crop_FU3, -1, kernel)

            FU_CROPS.append(sharp_FU3)

            with open('FU file num.txt', 'r') as h:
                count_FU = int(h.read().strip())
            # cv2.imshow("new crop3.png",sharp_FU3)
            cv2.imwrite(f"Forceps Utrata Tip/cropped_FU{count_FU}.png", sharp_FU3)
            with open(f'Forceps Utrata Tip/cropped_FU{count_FU}.txt', 'w') as c:
                c.write(f"{int(boxes.cls[i])} {xyxy[i][0]} {xyxy[i][1]} {xyxy[i][2]} {xyxy[i][3]}")
            with open("FU file num.txt", 'w') as h:
                h.write(str(count_FU + 1))
        else:
            i = i + 1
    FU_defect()


def crop_HS():
    global HS_CROPS
    xyxy = boxes.xyxy
    xywh =  boxes.xywh
    for i in range(len(boxes.cls)):
        if boxes.cls[i] == 3:
            crop_HS5 = img_tb[int(xyxy[i][1]-10):int(xyxy[i][3]+10), int(xyxy[i][0]):int(xyxy[i][2])]
            a_HS = int(xyxy[i][0]+xywh[i][2]+60)
            b_HS = int(xyxy[i][1]+xywh[i][2]+60)
            c_HS = int(xyxy[i][2]-xywh[i][2]-60)
            d_HS = int(xyxy[i][3]-xywh[i][2]-60)
            crop_HS6 = img_tb[int(xyxy[i][1]-60):int(b_HS), int(xyxy[i][0]-60):int(a_HS)]
            crop_HS7 = img_tb[d_HS:int(xyxy[i][3]+60), c_HS:int(xyxy[i][2]+60)]
            kernel = np.array([[0, -1,  0],
                               [-1,  5, -1],
                               [0, -1,  0]])
            sharp_HS5 = cv2.filter2D(crop_HS5, -1, kernel)

            HS_CROPS.append(sharp_HS5)

            with open('HS file num.txt', 'r') as j:
                count_HS = int(j.read().strip())
            # cv2.imshow("new crop4.png",sharp_HS5)
            cv2.imwrite(f"Hook Sinskey Tip/cropped_HS{count_HS}.png", sharp_HS5)
            with open(f'Hook Sinskey Tip/cropped_HS{count_HS}.txt', 'w') as d:
                d.write(f"{int(boxes.cls[i])} {xyxy[i][0]} {xyxy[i][1]} {xyxy[i][2]} {xyxy[i][3]}")
            with open("HS file num.txt", 'w') as j:
                j.write(str(count_HS + 1))
        else:
            i = i + 1
    HS_defect()


# save the prediction image of CP (cropped image and bounding box images)
def CP_defect():
    global CP_STATUS, _IMAGES
    if len(CP_CROPS) == 0:
        CP_STATUS = "missing"
        return

    # testing prediction for chop phaco
    with open('CP file num.txt', 'r') as f:
        count_CP = int(f.read().strip())

    model_CP = YOLO("Chop Phaco Tip2/runs/detect/train/weights/best.pt")
    result_CP = model_CP(source=f"Chop Phaco Tip2/cropped_CP{count_CP-1}.png", show=True, conf=0.1, verbose=False)
    result_CP[0].save(filename=f"Chop Phaco Tip2/CP_defect{count_CP-1}.png")

    # Store annotated image for API/UI
    if RUN_ID is not None:
        cp_annot = result_CP[0].plot()
        os.makedirs(OUT_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(OUT_DIR, f"Chop Phaco_annot_{RUN_ID}.png"), cp_annot)
        _IMAGES["Chop Phaco"] = cp_annot

    for results_CP in result_CP:
        if results_CP.boxes is None or len(results_CP.boxes) == 0:
            CP_STATUS = "non defective"
            return

        box_CP = results_CP.boxes.numpy()
        if box_CP.cls is None or len(box_CP.cls) == 0:
            CP_STATUS = "non defective"
            return

        class_name = results_CP.names[int(box_CP.cls[0])]
        # print("Chop Phaco:", class_name)

        cn = class_name.lower()
        CP_STATUS = "non defective" if "non" in cn else "defective"
        return

    CP_STATUS = "non defective"


# save the prediction image of FM (cropped image and bounding box images)
def FM_defect():
    global FM_STATUS, _IMAGES
    if len(FM_CROPS) == 0:
        FM_STATUS = "missing"
        return

    # prediction for forceps macpherson
    with open('FM file num.txt', 'r') as g:
        count_FM = int(g.read().strip())

    model_FM = YOLO("Forceps Macpherson Tip/runs/detect/train/weights/best.pt")
    result_FM= model_FM(source=f"Forceps Macpherson Tip/cropped_FM{count_FM-1}.png", show = True, conf = 0.1, verbose=False)
    result_FM[0].save(filename=f"Forceps Macpherson Tip/FM_defect{count_FM-1}.png")

    # Save + store annotated image for API/UI
    if RUN_ID is not None:
        fm_annot = result_FM[0].plot()
        os.makedirs(OUT_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(OUT_DIR, f"Forceps Macpherson_annot_{RUN_ID}.png"), fm_annot)
        _IMAGES["Forceps Macpherson"] = fm_annot

    for results_FM in result_FM:
        if results_FM.boxes is None or len(results_FM.boxes) == 0:
            FM_STATUS = "non defective"
            return

        box_FM = results_FM.boxes.numpy()
        if box_FM.cls is None or len(box_FM.cls) == 0:
            FM_STATUS = "non defective"
            return

        class_name = results_FM.names[int(box_FM.cls[0])]
        # print("Forceps Macpherson:", class_name)

        cn = class_name.lower()
        FM_STATUS = "non defective" if "non" in cn else "defective"
        return

    FM_STATUS = "non defective"


# save the prediction image of FU (cropped image and bounding box images)
def FU_defect():
    global FU_STATUS
    if len(FU_CROPS) == 0:
        FU_STATUS = "missing"
        return

    # prediction for forceps utrata
    with open('FU file num.txt', 'r') as h:
        count_FU = int(h.read().strip())

    model_FU = YOLO("Forceps Utrata Tip/FU(300)/runs/detect/train/weights/best.pt")
    result_FU = model_FU(source=f"Forceps Utrata Tip/cropped_FU{count_FU-1}.png", show = True, conf = 0.1, verbose=False)
    result_FU[0].save(filename=f"Forceps Utrata Tip/FU_defect{count_FU-1}.png")

    # Save + store annotated image for API/UI
    if RUN_ID is not None:
        fu_annot = result_FU[0].plot()
        os.makedirs(OUT_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(OUT_DIR, f"Forceps Utrata_annot_{RUN_ID}.png"), fu_annot)
        _IMAGES["Forceps Utrata"] = fu_annot

    for results_FU in result_FU:
        if results_FU.boxes is None or len(results_FU.boxes) == 0:
            FU_STATUS = "non defective"
            return

        box_FU = results_FU.boxes.numpy()
        if box_FU.cls is None or len(box_FU.cls) == 0:
            FU_STATUS = "non defective"
            return

        class_name = results_FU.names[int(box_FU.cls[0])]
        # print("Forceps Utrata:", class_name)

        cn = class_name.lower()
        FU_STATUS = "non defective" if "non" in cn else "defective"
        return

    FU_STATUS = "non defective"


# save the prediction image of HS  (cropped image and bounding box images)
def HS_defect():
    global HS_STATUS, _IMAGES
    if len(HS_CROPS) == 0:
        HS_STATUS = "missing"
        return

    with open('HS file num.txt', 'r') as j:
        count_HS = int(j.read().strip())

    model_HS = YOLO("Hook Sinskey Tip/runs/detect/train/weights/best.pt")
    result_HS= model_HS(source=f"Hook Sinskey Tip/cropped_HS{count_HS-1}.png", show = True, conf = 0.1, verbose=False)
    result_HS[0].save(filename=f"Hook Sinskey Tip/HS_defect{count_HS-1}.png")

    # Save + store annotated image for API/UI
    if RUN_ID is not None:
        hs_annot = result_HS[0].plot()
        os.makedirs(OUT_DIR, exist_ok=True)
        cv2.imwrite(os.path.join(OUT_DIR, f"HookSinskey_annot_{RUN_ID}.png"), hs_annot)
        _IMAGES["Hook Sinskey"] = hs_annot

    for results_HS in result_HS:
        if results_HS.boxes is None or len(results_HS.boxes) == 0:
            HS_STATUS = "non defective"
            return

        box_HS = results_HS.boxes.numpy()
        if box_HS.cls is None or len(box_HS.cls) == 0:
            HS_STATUS = "non defective"
            return

        class_name = results_HS.names[int(box_HS.cls[0])]
        # print("Hook Sinskey:", class_name)

        cn = class_name.lower()
        HS_STATUS = "non defective" if "non" in cn else "defective"
        return

    HS_STATUS = "non defective"


# save tool box images (original and bounding box images)
def save_TB():
    xyxy = boxes.xyxy
    with open('Whole toolbox/TB file num.txt', 'r') as k:
        count_TB = int(k.read().strip())

    cv2.imwrite(f"Whole toolbox/toolbox{count_TB}.png", img_tb)
    result_TB[0].save(filename=f"Whole toolbox/TB_detect{count_TB}.png")

    with open(f'Whole toolbox/toolbox{count_TB}.txt', 'w') as e:
        for i in range(len(boxes.cls)):
            e.write(f"{int(boxes.cls[i])} {xyxy[i][0]} {xyxy[i][1]} {xyxy[i][2]} {xyxy[i][3]}"+"\n")
    with open("Whole toolbox/TB file num.txt", 'w') as k:
        k.write(str(count_TB + 1))

    # print(boxes.cls[0])

    # Save + store annotated toolbox image for API/UI
    if RUN_ID is not None:
        os.makedirs(OUT_DIR, exist_ok=True)
        tb_annot = result_TB[0].plot()
        cv2.imwrite(os.path.join(OUT_DIR, f"Toolbox_annot_{RUN_ID}.png"), tb_annot)
        _IMAGES["toolbox"] = tb_annot


def analyze_image(img_bgr):
    global img_tb, result_TB, boxes
    global CP_CROPS, FM_CROPS, FU_CROPS, HS_CROPS
    global CP_STATUS, FM_STATUS, FU_STATUS, HS_STATUS
    global REPORT
    global RUN_ID, OUT_DIR, _IMAGES

    img_tb = img_bgr

    # NEW: init session/run
    RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # --- CLEAR OUTPUT FOLDER EACH RUN ---
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    _IMAGES = {}

    # reset per-call globals
    CP_CROPS, FM_CROPS, FU_CROPS, HS_CROPS = [], [], [], []
    CP_STATUS = FM_STATUS = FU_STATUS = HS_STATUS = "missing"

    # initialize report for API path
    REPORT = {"overall": "", "tools": [], "tool_status": {}, "_images": {}}

    # toolbox detection
    model_TB = YOLO("Whole toolbox/runs/detect/train/weights/best.pt")
    result_TB = model_TB(source=img_tb, show=True, conf=0.4, verbose=False)
    result_TB[0].show()
    b = result_TB[0].boxes

    if b is None or len(b) == 0:
        REPORT["overall"] = "Missing: Chop Phaco, Forceps Macpherson, Forceps Utrata, Hook Sinskey Tip"
        REPORT["tools"] = [
            {"name": "Chop Phaco", "count": 0, "status": "missing"},
            {"name": "Forceps Macpherson", "count": 0, "status": "missing"},
            {"name": "Forceps Utrata", "count": 0, "status": "missing"},
            {"name": "Hook Sinskey Tip", "count": 0, "status": "missing"},
        ]
        REPORT.pop("tool_status", None)
        # still return toolbox image if you want; but no detections means no plot boxes
        REPORT["_images"] = _IMAGES
        return REPORT

    boxes = b.numpy()

    # compute overall
    count_tools()

    # crop + defect + (optional) save_TB
    crop_img()
    save_TB()

    # counts from toolbox detections
    cp_count = int(np.sum(boxes.cls == 0))
    fm_count = int(np.sum(boxes.cls == 1))
    fu_count = int(np.sum(boxes.cls == 2))
    hs_count = int(np.sum(boxes.cls == 3))

    REPORT["tools"] = [
        {"name": "Chop Phaco", "count": cp_count, "status": ("missing" if cp_count == 0 else CP_STATUS)},
        {"name": "Forceps Macpherson", "count": fm_count, "status": ("missing" if fm_count == 0 else FM_STATUS)},
        {"name": "Forceps Utrata", "count": fu_count, "status": ("missing" if fu_count == 0 else FU_STATUS)},
        {"name": "Hook Sinskey Tip", "count": hs_count, "status": ("missing" if hs_count == 0 else HS_STATUS)},
    ]

    REPORT.pop("tool_status", None)
    # Provide annotated images to API: Keys MUST match tool names used above
    REPORT["_images"] = _IMAGES
    return REPORT

# put the path of the image in the () below and remove the "# " to run the code!! [only for debugging this code]

# '''
if __name__ == "__main__":
    test = cv2.imread(r"Testing/1.1_20260213_131502549.png")
    rep = analyze_image(test)
    print(rep["overall"])
    for t in rep["tools"]:
        print(t)
    print("\n--- IMAGE CHECK ---")
    print("Image keys:", rep.get("_images", {}).keys())
    print(rep)
# '''
