import cv2

from locate import locate_barcode
from read import read_barcode


def get_barcode_from_img(img_path):
    barcode_imgs = locate_barcode(img_path)
    results = []
    for img in barcode_imgs:
        cv2.imwrite("barcode_img.jpg", img)
        cv2.imshow("barcode_img", img)
        cv2.waitKey(0)
        barcode = read_barcode("barcode_img.jpg")
        print(barcode)
        if barcode is not None:
            results.append(barcode)
    if len(results) == 0:
        print("Nie znaleziono kodu kreskowego")
    else:
        barcode = max(set(results), key=results.count)
        print(f"Znaleziono kod kreskowy: {barcode}")
        return barcode

get_barcode_from_img("hunger.jpg")