"""
FastAPI 应用主文件
"""
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from comac_purchase.app.router.project import router as project_router
from comac_purchase.app.router.supplier import router as supplier_router
from comac_purchase.app.router.bid import router as bid_router
from comac_purchase.app.router.gen_tensor_file import router as llm_tool_router
from comac_purchase.app.router.llm_rename import router as llm_rename_router
from comac_purchase.app.router.llm_init_check import router as llm_init_check_router
from comac_purchase.db import init_db

app = FastAPI(
    title="商飞智能采购POC API",
    description="商飞智能采购POC后端API",
    version="1.0.0"
)

# 获取项目根目录
_project_root = Path(__file__).parent.parent.parent
_frontend_dist = _project_root / "front" / "dist"


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    print("数据库初始化完成")

# 配置CORS，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vite默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建API路由组（支持/api前缀，兼容前端配置）
api_router = APIRouter(prefix="/api")
api_router.include_router(project_router)
api_router.include_router(supplier_router)
api_router.include_router(bid_router)
api_router.include_router(llm_tool_router)
api_router.include_router(llm_rename_router)
api_router.include_router(llm_init_check_router)

# 注册API路由组（/api前缀）
app.include_router(api_router)

# 挂载前端静态文件目录（CSS、JS、图片等）
if _frontend_dist.exists():
    # 挂载assets目录
    assets_dir = _frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/")
async def serve_frontend():
    """根路径，返回前端index.html"""
    index_path = _frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {
        "message": "商飞智能采购POC API",
        "version": "1.0.0",
        "note": "前端资源未找到，请先构建前端项目"
    }


# SPA路由支持：所有未匹配的路由都返回index.html（必须在最后注册）
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """
    处理前端SPA路由（所有未匹配的路由都返回index.html）
    由于FastAPI按注册顺序匹配路由，这个catch-all路由只会匹配未被其他路由处理的路径
    """
    # 获取完整请求路径
    request_path = request.url.path
    
    # 排除 API 路由（/api 开头的路径应该已经被前面的路由处理了，这里只是双重保险）
    if request_path.startswith("/api"):
        raise HTTPException(status_code=404, detail="API资源未找到")
    
    # 排除静态资源路径（/assets 已经通过 mount 挂载，这里只是双重保险）
    if request_path.startswith("/assets"):
        raise HTTPException(status_code=404, detail="静态资源未找到")
    
    # 安全检查：防止路径遍历攻击
    if ".." in full_path:
        raise HTTPException(status_code=400, detail="非法路径")
    
    # 如果请求的是静态文件且文件存在，直接返回
    static_file_path = _frontend_dist / full_path
    # 确保文件在dist目录内（防止路径遍历）
    try:
        static_file_path.resolve().relative_to(_frontend_dist.resolve())
    except ValueError:
        # 如果路径不在dist目录内，直接返回index.html（可能是前端路由）
        index_path = _frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path), media_type="text/html")
        raise HTTPException(status_code=403, detail="访问被拒绝")
    
    if static_file_path.exists() and static_file_path.is_file():
        return FileResponse(str(static_file_path))
    
    # 否则返回index.html（支持前端路由）
    index_path = _frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    
    raise HTTPException(status_code=404, detail="前端资源未找到，请先构建前端项目")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

