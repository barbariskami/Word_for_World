import cv2
from pyzbar import pyzbar


def scan_barcode(url):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    # resp = urllib.request.urlopen(url)
    # file = np.asarray(bytearray(resp.read()), dtype="uint8")
    # image = cv2.imdecode(file, cv2.IMREAD_COLOR)

    image = cv2.imread(url)

    barcodes = pyzbar.decode(image)
    if not barcodes:
        # image = cv2.imdecode(file, cv2.IMREAD_GRAYSCALE)
        image = cv2.imread(url)
        barcodes = pyzbar.decode(image)
    if not barcodes:
        # image = cv2.imdecode(file, cv2.IMREAD_REDUCED_COLOR_4)
        image = cv2.imread(url)
        barcodes = pyzbar.decode(image)
    if not barcodes:
        # image = cv2.imdecode(file, cv2.IMREAD_REDUCED_COLOR_8)
        image = cv2.imread(url)
        barcodes = pyzbar.decode(image)
    if not barcodes:
        # image = cv2.imdecode(file, cv2.IMREAD_COLOR)
        image = cv2.imread(url)

        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=10.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        barcodes = pyzbar.decode(final)
        if not barcodes:
            gray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
            barcodes = pyzbar.decode(gray)
    if not barcodes:
        # image = cv2.imdecode(file, cv2.IMREAD_GRAYSCALE)
        image = cv2.imread(url)
        color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        lab = cv2.cvtColor(color, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=10.0, tileGridSize=(32, 32))
        cl = clahe.apply(l)

        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        barcodes = pyzbar.decode(final)

    return [barcode.data.decode("utf-8") for barcode in barcodes]
