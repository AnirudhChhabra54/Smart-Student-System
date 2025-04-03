import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Class for handling OCR processing of marksheets"""
    
    def __init__(self, config=None):
        """Initialize OCR processor with optional configuration"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image (np.ndarray): Input image in numpy array format
            
        Returns:
            np.ndarray: Preprocessed image
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Apply thresholding to preprocess the image
            threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            # Apply dilation to connect text components
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            dilation = cv2.dilate(threshold, kernel, iterations=1)

            # Apply erosion to remove noise
            erosion = cv2.erode(dilation, kernel, iterations=1)

            return erosion
        except Exception as e:
            self.logger.error(f"Error in image preprocessing: {str(e)}")
            raise

    def extract_text(self, image_path: str) -> str:
        """
        Extract text from image using OCR
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Extracted text from the image
        """
        try:
            # Read image using opencv
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image at path: {image_path}")

            # Preprocess the image
            processed_image = self.preprocess_image(image)

            # Perform OCR
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed_image, config=custom_config)

            return text.strip()
        except Exception as e:
            self.logger.error(f"Error in OCR text extraction: {str(e)}")
            raise

    def extract_marks(self, text: str) -> List[Dict[str, float]]:
        """
        Extract subject marks from OCR text
        
        Args:
            text (str): OCR extracted text
            
        Returns:
            List[Dict[str, float]]: List of dictionaries containing subject marks
        """
        try:
            marks_data = []
            # Regular expression pattern for finding subject and marks
            pattern = r'(\w+)\s*:\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)'
            
            matches = re.finditer(pattern, text)
            for match in matches:
                subject = match.group(1)
                marks_obtained = float(match.group(2))
                max_marks = float(match.group(3))
                
                marks_data.append({
                    'subject': subject,
                    'marks_obtained': marks_obtained,
                    'max_marks': max_marks
                })
            
            return marks_data
        except Exception as e:
            self.logger.error(f"Error in marks extraction: {str(e)}")
            raise

    def extract_student_info(self, text: str) -> Dict[str, str]:
        """
        Extract student information from OCR text
        
        Args:
            text (str): OCR extracted text
            
        Returns:
            Dict[str, str]: Dictionary containing student information
        """
        try:
            info = {}
            
            # Regular expressions for different fields
            patterns = {
                'roll_number': r'Roll(?:\s+)?(?:No|Number|#)?\s*[:.-]\s*(\w+)',
                'name': r'Name\s*[:.-]\s*([A-Za-z\s]+)',
                'class': r'Class\s*[:.-]\s*(\w+)',
                'term': r'Term|Semester\s*[:.-]\s*(\w+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, text)
                if match:
                    info[field] = match.group(1).strip()
                else:
                    info[field] = None
            
            return info
        except Exception as e:
            self.logger.error(f"Error in student info extraction: {str(e)}")
            raise

    def process_marksheet(self, image_path: str) -> Dict[str, any]:
        """
        Process marksheet image and extract all relevant information
        
        Args:
            image_path (str): Path to the marksheet image
            
        Returns:
            Dict[str, any]: Dictionary containing extracted information
        """
        try:
            # Extract text from image
            text = self.extract_text(image_path)
            
            # Extract student information
            student_info = self.extract_student_info(text)
            
            # Extract marks
            marks_data = self.extract_marks(text)
            
            # Calculate total and percentage
            total_obtained = sum(mark['marks_obtained'] for mark in marks_data)
            total_max = sum(mark['max_marks'] for mark in marks_data)
            percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
            
            return {
                'student_info': student_info,
                'marks_data': marks_data,
                'total_marks': {
                    'obtained': total_obtained,
                    'maximum': total_max,
                    'percentage': round(percentage, 2)
                }
            }
        except Exception as e:
            self.logger.error(f"Error in marksheet processing: {str(e)}")
            raise

def process_marksheet(image_path: str) -> Dict[str, any]:
    """
    Wrapper function for processing marksheet
    
    Args:
        image_path (str): Path to the marksheet image
        
    Returns:
        Dict[str, any]: Extracted information from marksheet
    """
    processor = OCRProcessor()
    return processor.process_marksheet(image_path)