from fastapi import FastAPI, UploadFile, File
from typing import List
from fastapi.openapi.utils import get_openapi
import json

app = FastAPI()

@app.post('/upload1')
async def upload1(files: List[UploadFile] = File(...)):
    pass

@app.post('/upload2')
async def upload2(files: list[UploadFile] = File(...)):
    pass

@app.post('/upload3')
async def upload3(files: list[UploadFile]):
    pass

@app.post('/upload4')
async def upload4(files: List[UploadFile]):
    pass

schema = get_openapi(title='t', version='1', routes=app.routes)
with open('schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
