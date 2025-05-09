import os
import asyncio
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Import your agent initializer
from agent import initialize_agent

load_dotenv()

app = FastAPI()

# Mount static directory for JS/CSS if exists
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates directory
templates = Jinja2Templates(directory="templates")

# Initialize agent on startup
@app.on_event("startup")
async def startup_event():
    global agent
    agent = await initialize_agent()

# Home page
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/query")
async def sse_query(message: str = Query(...)):
    async def event_generator():
        async for step in agent.astream(
            {"messages": [{"role": "user", "content": message}]},
            stream_mode="values",
            config={"configurable": {"thread_id": "webthread"}}
        ):
            # get the last message in this step
            msg = step["messages"][-1]

            # only stream if it's an AI/assistant message
            if getattr(msg, "type", None) == "ai":
                # strip out any “Source:” metadata if present
                text = msg.content
                if "Content:" in text:
                    _, body = text.split("Content:", 1)
                    text = body.strip()

                yield f"data: {text}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# JSON single-shot endpoint
@app.post("/api/json_query")
async def json_query(payload: dict):
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": payload.get("message", "")}]} ,
        config={"configurable": {"thread_id": "webapi"}}
    )
    return JSONResponse({"response": response.content})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", 8000)))
