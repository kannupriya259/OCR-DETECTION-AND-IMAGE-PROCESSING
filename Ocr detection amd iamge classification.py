import numpy as np
import cv2
from PIL import Image
import pytesseract
import re

def read_projection_matrix(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return np.array([list(map(float, line.split())) for line in lines])

def resize_image(image, target_size):
    return cv2.resize(image, target_size)

# File paths
image_file_path = r"C:\Users\vish9\Downloads\UVeye\image.jpg"  
projection_matrix_file_path = r"C:\Users\vish9\Downloads\UVeye\projMat.txt"  
coordinates_banner = r"C:\Users\vish9\Downloads\UVeye\coordinated.png"
banner_image_path = r"C:\Users\vish9\Downloads\UVeye\banner.jpg"  
scan_file= r"C:\Users\vish9\Downloads\UVeye\3d_scan.txt"
# Read projection matrix
projection_matrix = read_projection_matrix(projection_matrix_file_path)

#converting 3d input image to 2d using projection matrix 
with open(scan_file, 'r') as file:
    coordinates_lines = file.readlines()
xyz_coordinates = np.array([tuple(map(float, line.split(',')[:3])) for line in coordinates_lines])
homogeneous_coordinates = np.column_stack((xyz_coordinates, np.ones(len(xyz_coordinates))))

# Project 3D coordinates to 2D image coordinates
image_coordinates_homogeneous = np.dot(projection_matrix, homogeneous_coordinates.T).T
image_coordinates = image_coordinates_homogeneous[:, :2] / image_coordinates_homogeneous[:, 2, None]


# Read png image with ocr and detect the coordinates 
image = cv2.imread(image_file_path)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
coordinated_image = Image.open(coordinates_banner)
ocr_text = pytesseract.image_to_string(coordinated_image)
coordinate_pattern = r'\((-?\d+\.\d+), (-?\d+\.\d+), (-?\d+\.\d+)\)'
ocr_coordinates = [tuple(map(float, match.groups())) for match in re.finditer(coordinate_pattern, ocr_text)]
#print("OCR Coordinates:")
#print(ocr_coordinates)

# Convert OCR coordinates to numpy array
ocr_coordinates = np.array(ocr_coordinates)

# Adding homogeneous coordinate (1) to each OCR point
ocr_coordinates_homogeneous = np.column_stack((ocr_coordinates, np.ones(len(ocr_coordinates))))

# Projecting OCR coordinates to 2D image coordinates
coordinates_2d_homogeneous = np.dot(projection_matrix, ocr_coordinates_homogeneous.T).T
coordinates_2d = coordinates_2d_homogeneous[:, :2] / coordinates_2d_homogeneous[:, 2:]

#banner image
banner_image = cv2.imread(banner_image_path)

# Resized banner image according to the coordinates
target_size = (int(abs(coordinates_2d[1][0] - coordinates_2d[0][0])), int(abs(coordinates_2d[2][1] - coordinates_2d[0][1])))
resized_banner = resize_image(banner_image, target_size)

# Overlaying  resized banner image on the highlighted image with transparency
alpha = 1  
beta = 1 - alpha
image_with_transparent_banner = image.copy()
image_with_transparent_banner[int(coordinates_2d[0][1]):int(coordinates_2d[0][1]) + target_size[1], int(coordinates_2d[0][0]):int(coordinates_2d[0][0]) + target_size[0]] = cv2.addWeighted(resized_banner, alpha, image_with_transparent_banner[int(coordinates_2d[0][1]):int(coordinates_2d[0][1]) + target_size[1], int(coordinates_2d[0][0]):int(coordinates_2d[0][0]) + target_size[0]], beta, 0)

# Split the image into left and right facades
left_facade = image_with_transparent_banner[:, :int(coordinates_2d[0][0])]
right_facade = image_with_transparent_banner[:, int(coordinates_2d[0][0]):]

#  the right facade image display
cv2.imshow('Right Facade', right_facade)
cv2.waitKey(0)
cv2.destroyAllWindows()
