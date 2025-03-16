from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import asyncio
from typing import List, Optional
import google.generativeai as genai
import os
import requests
from bs4 import BeautifulSoup

# --- Configure Gemini API ---
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# --- FastAPI setup ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Pydantic Model ---
class SEOAnalysisRequest(BaseModel):
    main_url: str
    comparison_urls: Optional[List[str]] = None

# --- Helper: Fetch Webpage Content ---
async def fetch_page_content(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching URL: {e}")

# --- AI Task Functions ---
async def keyword_analysis(url: str, content: str) -> str:
    prompt = f"Analyze keywords from this page: {url}\nContent: {content}\nProvide keywords, search volume, traffic potential, business potential, search intent matching, and keyword modifiers."
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text

async def content_analysis(url: str, content: str) -> str:
    prompt = f"Analyze content, elements, and metadata of this page: {url}\nContent: {content}\nProvide recommendations."
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text

async def onpage_analysis(url: str, content: str) -> str:
    prompt = f"Analyze on-page SEO for this page: {url}\nContent: {content}\nProvide recommendations for titles, subheadings, internal linking, readability, and content optimization."
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text

async def linkbuilding(url: str) -> str:
    prompt = f"Analyze link building potential for this page: {url}\nProvide recommendations for creating backlinks and earning backlinks."
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text

async def visualizer(keyword_results: str, content_results: str, linkbuilding_results: str) -> str:
    prompt = f"Keyword Analysis Results: {keyword_results}\nContent Analysis Results: {content_results}\nLinkBuilding Results: {linkbuilding_results}\nGenerate tables/graphs for keywords, content, and linkbuilding recommendations."
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text

async def manager_check(results: str) -> str:
    prompt = f"Proofread and validate the following results:\n{results}\nProvide feedback on accuracy and consistency."
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text

# --- SEO Analysis Main Function ---
async def analyze_url(request: SEOAnalysisRequest, tasks_queue: asyncio.Queue):
    main_url = request.main_url
    content = await fetch_page_content(main_url)

    await tasks_queue.put("Keyword Analysis Started")
    keyword_results = await keyword_analysis(main_url, content)
    await tasks_queue.put("Keyword Analysis Completed")

    await tasks_queue.put("Content Analysis Started")
    content_results = await content_analysis(main_url, content)
    await tasks_queue.put("Content Analysis Completed")

    await tasks_queue.put("On Page Analysis Started")
    onpage_results = await onpage_analysis(main_url, content)
    await tasks_queue.put("On Page Analysis Completed")

    await tasks_queue.put("Link Building Analysis Started")
    linkbuilding_results = await linkbuilding(main_url)
    await tasks_queue.put("Link Building Analysis Completed")

    await tasks_queue.put("Visualization Started")
    visualizer_results = await visualizer(keyword_results, content_results, linkbuilding_results)
    await tasks_queue.put("Visualization Completed")

    all_results = (
        f"Keyword Results:\n{keyword_results}\n"
        f"Content Results:\n{content_results}\n"
        f"Visualizer Results:\n{visualizer_results}\n"
        f"Onpage Results:\n{onpage_results}\n"
        f"LinkBuilding Results:\n{linkbuilding_results}"
    )

    await tasks_queue.put("Manager AI Started")
    manager_results = await manager_check(all_results)
    await tasks_queue.put("Manager AI Completed")

    await tasks_queue.put("Analysis Completed")

    return {
        "keyword_results": keyword_results,
        "content_results": content_results,
        "visualizer_results": visualizer_results,
        "manager_results": manager_results,
        "onpage_results": onpage_results,
        "linkbuilding_results": linkbuilding_results,
    }

# --- Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze(request: SEOAnalysisRequest, background_tasks: BackgroundTasks):
    tasks_queue = asyncio.Queue()
    background_tasks.add_task(analyze_url, request, tasks_queue)
    return {"message": "Analysis started. Check /results for updates.", "task_id": id(tasks_queue)}

@app.get("/results/{task_id}")
async def get_results(task_id: int, request: Request):
    for queue in app.dependency_overrides.keys():
        if id(queue) == task_id:
            try:
                task_status = await queue.get_nowait()
                return {"status": task_status}
            except asyncio.QueueEmpty:
                return {"status": "Processing"}
    return {"status": "Task not found"}

app.dependency_overrides = {}
