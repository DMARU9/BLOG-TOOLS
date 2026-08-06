import json
import time
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional

from pytrends.request import TrendReq

from .config import PYTRENDS_SLEEP_SECONDS


@dataclass
class TrendResult:
    topic: str
    interest_over_time: List[dict]
    related_queries: List[str]
    high_trend_topics: Optional[List[str]] = None
    trend_score: float = 0.0
    recommendation: str = ""


def analyze_trend(topic: str) -> TrendResult:
    """Analyze Google Trends for a given topic."""
    pytrends = TrendReq(hl='ja-JP', tz=540)
    
    # Rate limiting: sleep before request
    time.sleep(PYTRENDS_SLEEP_SECONDS)
    
    try:
        pytrends.build_payload([topic], cat=0, timeframe='today 12-m', geo='JP', gprop='')
        
        # Interest over time
        interest_df = pytrends.interest_over_time()
        interest_data = []
        if not interest_df.empty:
            interest_data = interest_df[topic].to_dict()
            # Convert timestamps to strings for JSON serialization
            interest_data = [{str(k): v} for k, v in interest_data.items()]
        
        # Related queries
        related_queries = pytrends.related_queries()
        related_list = []
        if topic in related_queries:
            rising = related_queries[topic].get('rising')
            if rising is not None and not rising.empty:
                related_list = rising['query'].tolist()[:5]
        
        # Calculate trend score (simple average of last 3 months vs previous 3 months)
        trend_score = 50.0  # Default
        if not interest_df.empty:
            recent = interest_df[topic].tail(12).mean()
            previous = interest_df[topic].head(12).mean()
            if previous > 0:
                trend_score = min(100.0, (recent / previous) * 50)
        
        recommendation = f"トピック「{topic}」のトレンドスコアは {trend_score:.1f} です。"
        if trend_score > 70:
            recommendation += " 高い関心が見込まれます。"
        elif trend_score < 30:
            recommendation += " 関心が低めですが、ニッチな切り口が有効です。"

        return TrendResult(
            topic=topic,
            interest_over_time=interest_data,
            related_queries=related_list,
            trend_score=trend_score,
            recommendation=recommendation
        )
    except Exception as e:
        return TrendResult(
            topic=topic,
            interest_over_time=[],
            related_queries=[],
            recommendation=f"分析中にエラーが発生しました: {str(e)}"
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m blog_writer.trend_analyzer <topic>")
        sys.exit(1)
    
    topic = sys.argv[1]
    result = analyze_trend(topic)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
