import pytest
from unittest.mock import patch, MagicMock
from blog_writer.trend_analyzer import analyze_trend, TrendResult

def test_analyze_trend_returns_trend_result():
    with patch('blog_writer.trend_analyzer.TrendReq') as mock_trend:
        mock_instance = MagicMock()
        mock_trend.return_value = mock_instance
        
        # Mock interest_over_time
        import pandas as pd
        dates = pd.date_range('2023-01-01', periods=52, freq='W')
        mock_df = pd.DataFrame({'test_topic': [10] * 52}, index=dates)
        mock_instance.interest_over_time.return_value = mock_df
        
        # Mock related_queries
        mock_instance.related_queries.return_value = {
            'test_topic': {
                'rising': pd.DataFrame({'query': ['query1', 'query2'], 'value': [100, 90]}),
                'top': pd.DataFrame()
            }
        }
        
        result = analyze_trend("test_topic")
        
        assert isinstance(result, TrendResult)
        assert result.topic == "test_topic"
        assert len(result.related_queries) == 2
        assert result.trend_score > 0
