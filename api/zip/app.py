from fastapi import FastAPI, Request, HTTPException
import requests
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette import status
from starlette.responses import JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes.resume import resume_route
from routes.job import job_route

# from starlette.responses import

from config import config
from home import main_route
from models.responses import UnAuthorizatedRequest


def init_routers(app_: FastAPI) -> None:
    app_.include_router(main_route)
    app_.include_router(resume_route)
    app_.include_router(job_route)

def custom_openai():
    header = {"name": "Authorization",
              "in": "header",
              "description": "Put Dynamics 365 authentication",
              "required": True,
              "style": "simple"}
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="HREX AI API",
        terms_of_service="https://exquitech.com/terms",
        contact={
            "name": "Exquitech",
            "url": "http://exquitech.com/contact/",
            "email": "ahmed.jarada@exquitech.com",
        },
        license_info={
            "name": "Exquitech",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
        description="HREX AI API",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "/favicon.ico"
    }
    app.openapi_schema = openapi_schema
    paths = openapi_schema["paths"]
    for url, methods in paths.items():
        for method in methods:
            if methods[method].get("parameters"):
                methods[method]["parameters"].append(header)
            else:
                methods[method]["parameters"] = [header]

    return app.openapi_schema


def create_app() -> FastAPI:
    app_ = FastAPI(
        docs_url=None if config.ENV == "production" else "/docs",
        redoc_url=None if config.ENV == "production" else "/redoc",
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=False,
                allow_methods=["post, get"],
                allow_headers=["Authorization", "Content-Type", "Accept"],
            ),
        ],

    )
    init_routers(app_=app_)

    return app_


app = create_app()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.openapi = custom_openai


# Middleware
@app.middleware("validation")
async def add_ads_validation(request: Request, call_next):

    return await call_next(request)
# Handlers
class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request, exc):
#     return JSONResponse(UnAuthorizatedRequest(), status_code=exc.status_code)
# JSONResponse(
#         status_code=exc.status_code,
#         content=jsonable_encoder({"result": "error", "message": "Something went wrong!",
#                                   "errors": [{i: "This field is required!"} for i in exc.errors()[0]["loc"][1:]],
#                                   "body": exc.body}),
#     )


@app.exception_handler(RequestValidationError)
async def standard_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"result": "error", "message": "Missing data!",
                                  "errors": [{i: "This field is required!"} for i in exc.errors()[0]["loc"][1:]],
                                  "body": exc.body}),
    )


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse("static/img.png")
    