import cv2
import numpy as np

def get_binary_images(image_path):
    """Convert the image to binary using adaptive thresholding."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    binarized = []
    adaptive = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    binarized.append(adaptive)
    for i in range(10, 255, 20):
        ret, binary = cv2.threshold(image, i, 255, cv2.THRESH_BINARY_INV)
        binarized.append(binary)
    return binarized

def custom_lines(binary_image):
    edges = cv2.Canny(binary_image, 50, 150, apertureSize=3)
    # display edges
    # cv2.imshow("edges", edges)
    contours, hierarchy = cv2.findContours(edges, 1, 2)
    # get smaller dimension of the image
    smaller_dim = min(binary_image.shape)
    min_length = smaller_dim / 20
    lines = []
    # copy image and draw and display contours
    for cnt in contours:
        poly = cv2.approxPolyDP(cnt, 0.03 * cv2.arcLength(cnt, True), True)
        if 2 <= len(poly) <= 9:
            for i in range(len(poly)):
                if (i+1) < len(poly):
                    x1, y1 = poly[i][0]
                    x2, y2 = poly[i+1][0]
                    if np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) > min_length:
                        lines.append(((x1, y1), (x2, y2)))
    # display poly
    # draw lines
    for line in lines:
        (x1, y1), (x2, y2) = line
        cv2.line(binary_image, (x1, y1), (x2, y2), (128, 128, 128), 2)
    # display binary_image
    # cv2.imshow("lines", binary_image)
    return lines


def identify_barcode(lines, img_smaller_dim, angle_tolerance=2):
    """Identify the barcode as a group of several parallel lines."""
    barcode_candidates = []

    for i, line1 in enumerate(lines):
        (x1, y1), (x2, y2) = line1
        theta1 = np.arctan2(y2 - y1, x2 - x1)

        group = [line1]
        for j, line2 in enumerate(lines):
            if i == j:
                continue
            (x3, y3), (x4, y4) = line2

            avg_length = sum([np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) for (x1, y1), (x2, y2) in group]) / len(group)
            length = np.sqrt((x4 - x3) ** 2 + (y4 - y3) ** 2)
            if not avg_length * 0.5 < length < avg_length * 1.5:
                continue

            theta2 = np.arctan2(y4 - y3, x4 - x3)
            angle_difference = abs(np.degrees(theta1 - theta2))
            if angle_difference < angle_tolerance or abs(angle_difference - 180) < angle_tolerance:
                # calculate distance between two lines
                for member in group:
                    (x5, y5), (x6, y6) = member
                    # calculate distance between pairs of points
                    distances = []
                    distances.append(np.sqrt((x5 - x3) ** 2 + (y5 - y3) ** 2))
                    distances.append(np.sqrt((x5 - x4) ** 2 + (y5 - y4) ** 2))
                    distances.append(np.sqrt((x6 - x3) ** 2 + (y6 - y3) ** 2))
                    distances.append(np.sqrt((x6 - x4) ** 2 + (y6 - y4) ** 2))
                    distances.sort()
                    if distances[0] < img_smaller_dim // 20 and distances[1] < img_smaller_dim // 20:
                        group.append(line2)
                        break

        if len(group) >= 10:  # Barcode typically has multiple parallel lines
            barcode_candidates.append(group)

    barcode_candidates.sort(key=len, reverse=True)
    if len(barcode_candidates) == 0:
        return None
    return barcode_candidates[0]

def crop_barcode(image_path, barcode_lines):
    """Crop the barcode from the original image."""
    image = cv2.imread(image_path)
    rect = cv2.minAreaRect(np.array([point for line in barcode_lines for point in line]))
    box = cv2.boxPoints(rect)
    box = np.int32(box)
    # make the box 5% larger
    for i in range(4):
        box[i] = box[i] + 0.05 * (box[i] - rect[0])
    barcode_img = image.copy()
    cv2.drawContours(barcode_img, [box], 0, (0, 255, 0), 2)
    # cv2.imshow("barcode_loc", barcode_img)
    # create new image with only the barcode
    box = sorted(box, key=lambda x: x[0])
    one_side = sorted(box[:2], key=lambda x: x[1])
    other_side = sorted(box[2:], key=lambda x: x[1])
    box = [one_side[1], one_side[0], other_side[0], other_side[1]]
    barcode_img = image[int(box[1][1]):int(box[0][1]), int(box[1][0]):int(box[2][0])]
    # if the barcode is rotated, rotate it back
    if barcode_img.shape[0] > barcode_img.shape[1]:
        barcode_img = cv2.rotate(barcode_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    # cv2.imshow("barcode_img", barcode_img)
    return barcode_img


def locate_barcode(img_path):
    binary_image = get_binary_images(img_path)
    barcode_imgs = []
    for img in binary_image:
        lines = custom_lines(img)
        if len(lines) < 4:
            continue
        barcode_lines = identify_barcode(lines, img_smaller_dim=min(img.shape), angle_tolerance=2)
        if barcode_lines is None:
            continue
        barcode_img = crop_barcode(img_path, barcode_lines)
        barcode_imgs.append(barcode_img)
    return barcode_imgs