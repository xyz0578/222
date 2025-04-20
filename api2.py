from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import re
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
    text: str  # 改为接收任意文本输入
    download_images: bool = False
    save_dir: str = "images"

@app.post("/extract", response_model=XHSResponse)
async def extract_content(request: XHSRequest):
    """
    从输入文本中提取小红书链接并获取内容
    """
    try:
        # 提取URL的正则表达式
        url_pattern = r'https?://(?:www\.)?(?:xiaohongshu\.com|xhslink\.com)/[^\s<>"\']+(?<![\s.,])'
        urls = re.findall(url_pattern, request.text)
        
        if not urls:
            raise HTTPException(status_code=400, detail="未在输入文本中找到有效的小红书链接")
        
        # 使用第一个找到的URL
        url = urls[0]
        print(f"从文本中提取的URL: {url}")  # 调试信息
        
        content = extract_xhs_content(url)
        
        if not content:
            print("内容提取失败，返回为空")  # 调试信息
            raise HTTPException(status_code=400, detail="无法提取内容，请检查链接是否有效")
        
        print(f"成功提取内容: {content}")  # 调试信息
        
        if request.download_images and content['image_urls']:
            downloaded_paths = download_images(content['image_urls'], request.save_dir)
            if not downloaded_paths:
                raise HTTPException(status_code=500, detail="图片下载失败")
        
        return content
        
    except Exception as e:
        print(f"发生错误: {str(e)}")  # 调试信息
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

@app.get("/")
async def root():
    """
    API 根路径，返回简单的欢迎信息
    """
    return {"message": "欢迎使用小红书内容提取 API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)