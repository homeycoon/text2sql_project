from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage

from graph.graph import graph_compile
from graph.states import GraphState

app = FastAPI(
    title="Text2SQL service"
)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "form.html", context={
            "request": request,
        }
    )


@app.post("/start_graph", response_model=None)
async def start_graph_process(
        request: Request,
        user_request: str = Form(...),
):
    initial_state = GraphState(
        messages=[],
        initial_message=HumanMessage(content=user_request),
        valid_result=None,
        final_result=None,
    )
    final_state = await graph_compile.ainvoke(initial_state)
    return final_state["final_result"]
