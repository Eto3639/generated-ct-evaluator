import numpy as np
import SimpleITK as sitk
from .base import QAModule

class TemporalMotion(QAModule):
    def __init__(self):
        super().__init__("TemporalMotion")

    def validate(self, data: dict) -> dict:
        """
        Validates 4D temporal consistency and mechanics.
        Input data:
        - '4d_ct': List of 3D numpy arrays or a 4D array (Phases).
        - 'respiratory_signal': 1D array (External surrogate, optional).
        """
        phases = data.get('4d_ct')
        if phases is None or len(phases) < 2:
            return {"status": "ERROR", "message": "Insufficient 4D data"}

        # Convert numpy phases to SimpleITK images for processing
        sitk_phases = [sitk.GetImageFromArray(p) for p in phases]

        # 1. Jacobian Determinant Analysis (Phase-to-Phase)
        jacobian_stats = []
        for i in range(len(sitk_phases) - 1):
            fixed = sitk_phases[i]
            moving = sitk_phases[i+1]

            # Perform DIR (Fast/Demons for QA check)
            # In production, use high-quality registration or pre-calculated fields
            transform = self._perform_dir(fixed, moving)

            # Calculate Jacobian
            min_j, max_j, neg_frac = self._calculate_jacobian_stats(transform)
            jacobian_stats.append({
                "phase_pair": f"{i}->{i+1}",
                "min_jacobian": min_j,
                "max_jacobian": max_j,
                "negative_jacobian_fraction": neg_frac
            })

        self.results['jacobian_analysis'] = jacobian_stats

        # 2. Respiratory Phase Validation & Smoothness
        # Extract diaphragm signal (simplified: Z-centroid of lung mask or lowest intensity gradient)
        # We will use Center of Mass of the volume as a proxy for bulk motion
        centroids = [self._get_centroid(p) for p in phases]
        z_trajectory = [c[0] for c in centroids] # Z-axis motion

        smoothness_score = self._analyze_smoothness(z_trajectory)
        self.results['trajectory_smoothness'] = smoothness_score

        # Check for spikes
        if smoothness_score < 0.8: # Threshold
             self.status = "FAIL"
        else:
             self.status = "PASS"

        # Check Jacobian failure (Negative Jacobian = Folding)
        for stat in jacobian_stats:
            if stat['negative_jacobian_fraction'] > 0.01: # >1% folding
                self.status = "FAIL"
                break

        return self.results

    def _perform_dir(self, fixed, moving):
        """Performs a fast Demons registration."""
        matcher = sitk.HistogramMatchingImageFilter()
        matcher.SetNumberOfHistogramLevels(1024)
        matcher.SetNumberOfMatchPoints(7)
        matcher.ThresholdAtMeanIntensityOn()
        moving = matcher.Execute(moving, fixed)

        demons = sitk.FastSymmetricForcesDemonsRegistrationFilter()
        demons.SetNumberOfIterations(10) # Low iterations for speed in this demo
        demons.SetStandardDeviations(1.0)

        displacement_field = demons.Execute(fixed, moving)
        return displacement_field

    def _calculate_jacobian_stats(self, displacement_field):
        """Calculates Jacobian Determinant statistics."""
        jacobian_filter = sitk.DisplacementFieldJacobianDeterminantFilter()
        jacobian_image = jacobian_filter.Execute(displacement_field)

        jacobian_arr = sitk.GetArrayFromImage(jacobian_image)

        min_j = float(np.min(jacobian_arr))
        max_j = float(np.max(jacobian_arr))

        # Negative Jacobian means non-physical folding
        negative_fraction = np.sum(jacobian_arr < 0) / jacobian_arr.size

        return min_j, max_j, float(negative_fraction)

    def _get_centroid(self, arr):
        from scipy.ndimage import center_of_mass
        # Simple intensity weighted centroid
        return center_of_mass(arr)

    def _analyze_smoothness(self, signal):
        """
        Analyzes smoothness using Total Variation or discrete differences.
        Returns a score 0-1 (1 is perfect).
        """
        signal = np.array(signal)
        # Normalize
        if np.max(signal) != np.min(signal):
            signal = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))

        # Calculate second derivative (acceleration)
        # Smooth motion has low acceleration changes
        accel = np.diff(signal, n=2)

        # If acceleration spikes, score drops
        max_accel = np.max(np.abs(accel)) if len(accel) > 0 else 0

        # Heuristic score
        score = np.exp(-max_accel)
        return float(score)
