import pandas as pd
from typing import List, Dict, Any
from .logger import data_parsing_logger

class ThresholdTracker:
    @staticmethod
    def detect_threshold_exits(filings_df: pd.DataFrame, threshold: float = 5.0) -> pd.DataFrame:
        """
        Detect shareholders falling below ownership threshold
        
        :param filings_df: DataFrame of SEC filings
        :param threshold: Ownership percentage threshold
        :return: DataFrame of threshold exits
        """
        try:
            # Sort filings by owner and filing date
            sorted_filings = filings_df.sort_values(['beneficial_owner', 'filing_date'])
            
            # Group by beneficial owner
            threshold_exits = []
            for owner, group in sorted_filings.groupby('beneficial_owner'):
                for i in range(1, len(group)):
                    prev_ownership = float(group.iloc[i-1]['ownership_percentage'])
                    curr_ownership = float(group.iloc[i]['ownership_percentage'])
                    
                    # Check if ownership drops below threshold
                    if prev_ownership > threshold and curr_ownership <= threshold:
                        exit_record = {
                            'beneficial_owner': owner,
                            'exit_date': group.iloc[i]['filing_date'],
                            'previous_ownership': prev_ownership,
                            'current_ownership': curr_ownership,
                            'company_name': group.iloc[i].get('company_name', 'N/A'),
                            'cusip': group.iloc[i].get('cusip', 'N/A')
                        }
                        threshold_exits.append(exit_record)
            
            exits_df = pd.DataFrame(threshold_exits)
            data_parsing_logger.info(f'Detected {len(exits_df)} threshold exits')
            return exits_df
        
        except Exception as e:
            data_parsing_logger.error(f'Threshold exit detection error: {e}')
            return pd.DataFrame()

    @staticmethod
    def analyze_threshold_patterns(threshold_exits: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze patterns in threshold exits
        
        :param threshold_exits: DataFrame of threshold exits
        :return: Dictionary of threshold exit analysis
        """
        try:
            if threshold_exits.empty:
                return {}
            
            analysis = {
                'total_exits': len(threshold_exits),
                'unique_owners': threshold_exits['beneficial_owner'].nunique(),
                'avg_ownership_before_exit': threshold_exits['previous_ownership'].mean(),
                'most_frequent_exits': threshold_exits['beneficial_owner'].value_counts().head(),
                'exit_distribution_by_year': threshold_exits.groupby(threshold_exits['exit_date'].str[:4]).size()
            }
            
            data_parsing_logger.info('Completed threshold exit pattern analysis')
            return analysis
        
        except Exception as e:
            data_parsing_logger.error(f'Threshold exit pattern analysis error: {e}')
            return {}

def track_ownership_thresholds(filings_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Comprehensive ownership threshold tracking
    
    :param filings_df: DataFrame of SEC filings
    :return: Dictionary of threshold tracking results
    """
    tracker = ThresholdTracker()
    
    try:
        # Detect threshold exits
        threshold_exits = tracker.detect_threshold_exits(filings_df)
        
        # Analyze exit patterns
        exit_analysis = tracker.analyze_threshold_patterns(threshold_exits)
        
        return {
            'threshold_exits': threshold_exits,
            'exit_analysis': exit_analysis
        }
    
    except Exception as e:
        data_parsing_logger.critical(f'Comprehensive threshold tracking failed: {e}')
        raise
