import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformancePredictor:
    """Class for predicting student performance using ML"""
    
    def __init__(self):
        """Initialize the predictor with ML models"""
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.logger = logging.getLogger(__name__)

    def _prepare_features(self, student_data: Dict) -> np.ndarray:
        """
        Prepare feature vector from student data
        
        Args:
            student_data (Dict): Dictionary containing student information
            
        Returns:
            np.ndarray: Prepared feature vector
        """
        try:
            features = []
            
            # Academic performance features
            features.extend([
                float(student_data.get('previous_grade', 0)),
                float(student_data.get('attendance_percentage', 0)),
                float(student_data.get('assignment_completion_rate', 0)),
                float(student_data.get('class_participation_score', 0))
            ])
            
            # Study pattern features
            features.extend([
                float(student_data.get('study_hours_per_week', 0)),
                float(student_data.get('self_study_score', 0)),
                float(student_data.get('group_study_score', 0))
            ])
            
            # Engagement metrics
            features.extend([
                float(student_data.get('submission_timeliness', 0)),
                float(student_data.get('extra_curricular_participation', 0)),
                float(student_data.get('project_scores', 0))
            ])
            
            return np.array(features).reshape(1, -1)
        except Exception as e:
            self.logger.error(f"Error in feature preparation: {str(e)}")
            raise

    def train(self, training_data: List[Dict], labels: List[float]):
        """
        Train the ML model with historical data
        
        Args:
            training_data (List[Dict]): List of student data dictionaries
            labels (List[float]): Corresponding performance labels
        """
        try:
            # Prepare feature matrix
            X = np.array([self._prepare_features(data).flatten() for data in training_data])
            y = np.array(labels)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True
            
            self.logger.info("Model training completed successfully")
        except Exception as e:
            self.logger.error(f"Error in model training: {str(e)}")
            raise

    def predict(self, student_data: Dict) -> Dict[str, any]:
        """
        Predict student performance
        
        Args:
            student_data (Dict): Student information and metrics
            
        Returns:
            Dict[str, any]: Prediction results and confidence metrics
        """
        try:
            if not self.is_trained:
                raise ValueError("Model not trained yet")
            
            # Prepare and scale features
            X = self._prepare_features(student_data)
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            predicted_score = self.model.predict(X_scaled)[0]
            
            # Calculate confidence score (using prediction probabilities)
            confidence_score = min(
                max(
                    0.5 + abs(predicted_score - 70) / 100,  # Base confidence on distance from average
                    0.1  # Minimum confidence
                ),
                0.95  # Maximum confidence
            )
            
            # Determine predicted grade
            predicted_grade = self._score_to_grade(predicted_score)
            
            # Get feature importances
            importance_factors = self._get_importance_factors(student_data)
            
            return {
                'predicted_score': round(predicted_score, 2),
                'predicted_grade': predicted_grade,
                'confidence_score': round(confidence_score, 2),
                'importance_factors': importance_factors,
                'prediction_date': datetime.utcnow().isoformat(),
                'model_version': '1.0'
            }
        except Exception as e:
            self.logger.error(f"Error in performance prediction: {str(e)}")
            raise

    def _score_to_grade(self, score: float) -> str:
        """
        Convert numerical score to letter grade
        
        Args:
            score (float): Numerical score
            
        Returns:
            str: Letter grade
        """
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'

    def _get_importance_factors(self, student_data: Dict) -> List[Dict[str, any]]:
        """
        Get most important factors affecting the prediction
        
        Args:
            student_data (Dict): Student information and metrics
            
        Returns:
            List[Dict[str, any]]: List of important factors and their impacts
        """
        feature_names = [
            'previous_grade', 'attendance', 'assignment_completion',
            'class_participation', 'study_hours', 'self_study',
            'group_study', 'submission_timeliness', 'extra_curricular',
            'project_scores'
        ]
        
        # Get feature importances from model
        importances = self.model.feature_importances_
        
        # Sort features by importance
        factors = []
        for name, importance in zip(feature_names, importances):
            if importance > 0.05:  # Only include significant factors
                factors.append({
                    'factor': name,
                    'importance': round(float(importance), 3),
                    'current_value': student_data.get(name, 0)
                })
        
        return sorted(factors, key=lambda x: x['importance'], reverse=True)

def predict_performance(student_data: Dict) -> Dict[str, any]:
    """
    Wrapper function for performance prediction
    
    Args:
        student_data (Dict): Student information and metrics
        
    Returns:
        Dict[str, any]: Prediction results
    """
    predictor = PerformancePredictor()
    
    # In a real application, we would load a pre-trained model here
    # For demonstration, we'll use some dummy training data
    dummy_training_data = [
        {'previous_grade': 85, 'attendance_percentage': 90, 'assignment_completion_rate': 95},
        {'previous_grade': 75, 'attendance_percentage': 80, 'assignment_completion_rate': 85},
        {'previous_grade': 65, 'attendance_percentage': 70, 'assignment_completion_rate': 75}
    ]
    dummy_labels = [87, 78, 68]
    
    predictor.train(dummy_training_data, dummy_labels)
    return predictor.predict(student_data)