from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Serve static files (CSS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")


# ---------------- Routes ---------------- #

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    main_url: str = Form(...),
    comparison_urls: str = Form("")
):
    # Parse comparison URLs
    comparison_list = [url.strip() for url in comparison_urls.split(",") if url.strip()]

    # --- Agent Simulations ---
    keyword_result = keyword_analysis_agent(main_url)
    content_result = content_analysis_agent(main_url)
    visual_result = visualizer_agent(main_url)
    manager_result = manager_ai_agent(main_url, comparison_list)
    onpage_result = onpage_analysis_agent(main_url)
    linkbuilding_result = link_building_agent(main_url)

    results = {
        "main_url": main_url,
        "comparison_urls": comparison_list,
        "keyword_result": keyword_result,
        "content_result": content_result,
        "visual_result": visual_result,
        "manager_result": manager_result,
        "onpage_result": onpage_result,
        "linkbuilding_result": linkbuilding_result,
    }

    return templates.TemplateResponse("results.html", {"request": request, "results": results})


# ---------------- Agent Functions ---------------- #

def keyword_analysis_agent(url: str) -> str:
    return f"Extracted primary keywords from {url} and identified keyword density."

def content_analysis_agent(url: str) -> str:
    return f"Analyzed text content of {url} for SEO quality, headings, and readability."

def visualizer_agent(url: str) -> str:
    return f"Created visual summary for {url}'s SEO metrics (placeholder)."

def manager_ai_agent(url: str, comparisons: list) -> str:
    if comparisons:
        return f"Compared {url} with {len(comparisons)} competitor URLs and summarized findings."
    else:
        return "No comparison URLs provided. Manager AI focused on the main URL only."

def onpage_analysis_agent(url: str) -> str:
    return f"Checked {url} for meta tags, image alt texts, and internal link structure."

def link_building_agent(url: str) -> str:
    return f"Suggested potential backlinks and outreach strategies for {url}."
