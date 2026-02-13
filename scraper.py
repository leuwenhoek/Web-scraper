import requests
import os
import nltk
import time
from ddgs import DDGS
from ollama import chat
from pathlib import Path
from trends import Trend
from bs4 import BeautifulSoup
from plyer import notification
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.parsers.plaintext import PlaintextParser
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

console = Console()

class Prompt():
    def __init__(self):
        pass

    def format_summary(self):
        cmd = """
You are a Senior Research Analyst. Take the provided CONTEXT and CONTENT and write a comprehensive, high-level briefing.

OUTPUT REQUIREMENTS:
- Length: 2-3 detailed paragraphs (approx. 200-300 words).
- Tone: Professional, objective, and insight-driven.
- Structure:
   1. Executive Overview: What happened? (The core news).
   2. Deep Dive & Data: Specific numbers, quotes, names, and technical details found in the text.
   3. Strategic Implication: Why does this matter? (Future outlook, market impact).

STRICT RULES:
- Do NOT use filler phrases like "The article discusses..." or "It is mentioned that...". Start directly with the facts.
- If dates or statistics are present in the text, you MUST include them.
- Avoid generic summaries; aim for "White Paper" quality.

YOUR TURN: [Insert context and content here]
"""
        return cmd

    def top_topic(self, topics):
        topics_str = ", ".join(str(topic) for topic in topics)
        cmd = f'''
You are a Viral Trend Analyst and Editor-in-Chief. 
I have a list of trending keywords/topics: {topics_str}

YOUR TASK:
Identify the single most high-impact topic from this list. 
Prioritize topics that are:
1. "News-Worthy" (Global events, tech breakthroughs, finance).
2. Actionable (Something people want to read about right now).

OUTPUT FORMAT:
Provide the response in this EXACT format:
"Topic: <Topic_Name> | Insight: <1 sentence explaining why this is the best pick>"

YOUR TURN:
'''
        return cmd

    def X_post(self, summary):
        cmd = f'''
Create ONE X (Twitter) post based on this detailed summary: {summary}

STRICT GUIDELINES:
- MAX 280 characters.
- Style: Industry Insider. Provocative but factual.
- Structure: Hook -> Data Point -> Question/Insight.
- Use 1-2 relevant hashtags.

Output ONLY the post text.
'''
        return cmd


class Location:
    def __init__(self):
        pass
    
    def output_locate(self):
        return os.path.join(Path(__file__).parent,'output.txt') 
    
    def summary_locate(self):
        return os.path.join(Path(__file__).parent,'summary.txt')

    def post(self,of):
        folder = os.path.join(Path(__file__).parent,'post')
        if not os.path.exists(folder): os.mkdir(folder)
        
        if of.lower() == 'x':
            return os.path.join(folder,'X.txt')
        elif of.lower() == 'linkedin':
            return os.path.join(folder,'LinkedIn.txt')
        raise Exception('Platform not found') 
    
class Create_Post:
    def __init__(self):
        pass

    def X(self,summary):
        return load_model(model,prompt.X_post(summary))
    
    def LinkedIn(self):
        return "Creating LinkedIn post"

loc = Location()
prompt = Prompt()
post = Create_Post()
model = 'phi'

def init():
    for path in [loc.output_locate(), loc.summary_locate(), loc.post('x')]:
        if os.path.exists(path): os.remove(path)
    return 0

def read_output():
    with open(loc.output_locate(),'r',encoding='utf-8') as f:
        return f.read()

def save_data(location,data):
    with open(location,'a',encoding='utf-8') as f:
        f.write(data + "\n")

def beautify_html(html_content):
    soup = BeautifulSoup(html_content,'html.parser')
    tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    return '\n'.join(t.get_text(strip=True) for t in tags).strip()

def relevant_sites(search_about):
    with DDGS() as ddgs:
        return [r['href'] for r in list(ddgs.text(search_about, max_results=5))]

def scrape_sites(search_for):
    sites = relevant_sites(search_about=search_for)
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task(description="Scraping web data...", total=len(sites))
        for site in sites:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                page = requests.get(site, headers=headers, timeout=10)
                page.raise_for_status()
                save_data(loc.output_locate(), beautify_html(page.content))
            except Exception:
                pass
            progress.update(task, advance=1)

def summary():
    try: nltk.data.find('tokenizers/punkt')
    except LookupError: nltk.download('punkt', quiet=True)

    parser = PlaintextParser(read_output(), Tokenizer("english"))
    summarizer = LuhnSummarizer(Stemmer("english"))
    summarizer.stop_words = get_stop_words("english")
    
    res = summarizer(parser.document, 10)
    summary_text = ' '.join(str(s) for s in res)
    save_data(loc.summary_locate(), summary_text)
    return summary_text

def load_model(model_name, prompt_text):
    response = chat(model=model_name, messages=[{'role': 'user', 'content': prompt_text}])
    return response.message.content

def trending(keyword):
    trend = Trend()
    trend.analyze_trends(keyword)
    topics = trend.get_related_topics(keyword)
    return load_model(model, prompt.top_topic(topics))

def send_notification(title,msg):
    try:
        notification.notify(title=title, message=msg, timeout=3, app_name="Post Automation")        #type: ignore
    except: pass

def main():
    console.clear()
    
    header_panel = Panel(
        Align.center("[bold cyan]AI CONTENT AUTOMATION ENGINE[/bold cyan]"),
        subtitle="v2.0 - Research & Social",
        border_style="cyan"
    )
    rprint(header_panel)

    keyword = console.input("[bold yellow]Enter trend keyword (e.g. AI, Finance, Space): [/bold yellow]")
    
    
    while True:
        with console.status("[bold green]Analyzing market trends...") as status:
            best_topic = trending(keyword)

        rprint(Panel(f"[bold white]{best_topic}[/bold white]", title="AI Strategy Recommendation", border_style="green"))
        send_notification("AI Strategy Recommendation", "AI Strategy Recommendation is ready.")
        recommendation_repeat = console.input("[bold red]What another Recommendation (y/n): [/bold red]")

        if recommendation_repeat.lower() == 'n':
            break
    
    search_for = console.input("[bold yellow]What specific topic should I research? [/bold yellow]")
    scrape_sites(search_for)
    
    while True:    
        with console.status("[bold magenta]Synthesizing research summary...") as status:
            raw_summary = summary()
            summary_response = load_model(model, f"Topic: {search_for}\n\n-Summary:\n{raw_summary}\n\nInstructions:\n{prompt.format_summary()}\n\nReturn ONLY the new summary:")
            rprint(Panel(f"[bold white]{summary_response}[/bold white]", title="AI Summary", border_style="green"))
        send_notification("Summary Created", "Summary is ready.")
        summary_repeat = console.input("[bold red]What another Summary (y/n): [/bold red]")

        if summary_repeat.lower() == 'n':
            break

    save_data(loc.summary_locate(), summary_response)
    rprint(f"[bold green]✔[/bold green] Deep-dive summary saved to: [underline]{loc.summary_locate()}[/underline]")

    while True:    
        with console.status("[bold blue]Crafting social media post...") as status:
            x_content = post.X(summary_response)
            save_data(loc.post('x'), x_content)
        send_notification("Post Created", "Post(s) are ready.")
        post_repeat = console.input("[bold red]What another Summary (y/n): [/bold red]")

        if post_repeat.lower() == 'n':
            break
    
    rprint(Panel(x_content if x_content is not None else "[No X post generated]", title="Generated X Post", border_style="blue"))
    rprint("\n[bold cyan]Process Complete![/bold cyan] 🚀")
    send_notification("Workflow Finished", "Research and Post are ready.")

if __name__ == "__main__":
    init()
    main()