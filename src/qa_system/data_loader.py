import SimpleITK as sitk
import numpy as np
import os

class DataLoader:
    """Utility class to load medical images from various formats."""

    @staticmethod
    def load_image(path: str):
        """Loads an image (DICOM, NIfTI, NRRD, etc.) using SimpleITK."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")

        if os.path.isdir(path):
            # Try to load as DICOM series
            reader = sitk.ImageSeriesReader()
            dicom_names = reader.GetGDCMSeriesFileNames(path)
            if not dicom_names:
                raise ValueError(f"No DICOM series found in directory: {path}")
            reader.SetFileNames(dicom_names)
            image = reader.Execute()
        else:
            # Try to load as a single file (NIfTI, NRRD, etc.)
            image = sitk.ReadImage(path)

        return image

    @staticmethod
    def to_numpy(image: sitk.Image):
        """Converts SimpleITK image to numpy array."""
        return sitk.GetArrayFromImage(image)

    @staticmethod
    def get_metadata(image: sitk.Image):
        """Extracts key metadata from SimpleITK image."""
        return {
            "spacing": image.GetSpacing(),
            "origin": image.GetOrigin(),
            "direction": image.GetDirection(),
            "size": image.GetSize()
        }

    @staticmethod
    def load_and_preprocess(path: str):
        """Helper to load image and return both array and metadata."""
        img = DataLoader.load_image(path)
        return DataLoader.to_numpy(img), DataLoader.get_metadata(img)
