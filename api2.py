from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from xhs import extract_xhs_content, download_images

app = FastAPI(
    title="小红书内容提取 API",
    description="用于从小红书链接中提取标题、正文和配图的 API 服务",
    version="1.0.0"
)

class XHSResponse(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_urls: List[str] = []
    likes: Optional[str] = None
    comments: Optional[str] = None
    collects: Optional[str] = None

class XHSRequest(BaseModel):
    url: HttpUrl
    download_images: bool = False
    save_dir: str = "images"

@app.post("/extract", response_model=XHSResponse)
async def extract_content(request: XHSRequest):
    """
    从小红书链接中提取内容
    """
    content = extract_xhs_content(str(request.url))
    
    if not content:
        raise HTTPException(status_code=400, detail="无法提取内容，请检查链接是否有效")
    
    if request.download_images and content['image_urls']:
        downloaded_paths = download_images(content['image_urls'], request.save_dir)
        if not downloaded_paths:
            raise HTTPException(status_code=500, detail="图片下载失败")
    
    return content

@app.get("/")
async def root():
    """
    API 根路径，返回简单的欢迎信息
    """
    return {"message": "欢迎使用小红书内容提取 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)