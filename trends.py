from pytrends.request import TrendReq
from ddgs import DDGS

class Trend:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)
    
    def get_related_topics(self, keyword):
        base_topics = [
            f"{keyword} trends 2026",
            f"{keyword} latest news", 
            f"top {keyword} startups",
            f"{keyword} tutorial",
            f"{keyword} tools",
            f"best {keyword} platforms",
            f"{keyword} future",
            f"{keyword} india"
        ]
        
        topics = []
        try:
            with DDGS() as ddgs:
                results = ddgs.text(f"{keyword} related topics", max_results=10)
                for r in results:
                    topics.append(r['title'][:60])
        except:
            topics = base_topics
        
        return topics

    def analyze_trends(self, keyword):
        """Get trending data + related topics for ANY keyword"""
        print(f"\n{'='*60}")
        print(f"🔥 TRENDING ANALYSIS: '{keyword.upper()}'")
        print(f"{'='*60}")
        
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([keyword], cat=0, timeframe='today 3-m', geo='')
        country_data = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
        
        scores = {}
        for country in ['India', 'United States', 'Germany', 'United Kingdom', 'France']:
            if country in country_data.index:
                scores[country] = country_data.loc[country, keyword]
            else:
                scores[country] = "Low volume"
        
        top_global = country_data[keyword].sort_values(ascending=False).head(5)
        
        print(f"\n📈 COUNTRY SCORES (0-100):")
        print("🇮🇳 India:", scores['India'])
        print("🇺🇸 United States:", scores['United States']) 
        print("🇪🇺 Europe Average:")
        print(f"   - Germany: {scores['Germany']}")
        print(f"   - UK: {scores['United Kingdom']}")
        print(f"   - France: {scores['France']}")
        print(f"\n🏆 TOP 5 GLOBAL: {top_global.to_dict()}")
        
        print(f"\n🔍 RECOMMENDED RELATED TOPICS:")
        related = self.get_related_topics(keyword)
        for i, topic in enumerate(related[:8], 1):
            print(f"{i}. {topic}")
        
        print(f"\n💡 TREND INSIGHTS:")
        print(f"• Max interest: {country_data[keyword].max()}/100")
        print(f"• Hottest market: {country_data[keyword].idxmax()}")

if __name__ == "__main__":
    keyword = input("🎯 Enter keyword/sentence: ")
    trend = Trend()
    trend.analyze_trends(keyword)
