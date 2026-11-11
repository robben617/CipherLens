from fastapi import APIRouter

from services.glossary import TERMS

router = APIRouter(prefix="/api", tags=["术语表"])


@router.get("/glossary", summary="术语表（与前端 data/glossary.ts 同源）")
def read_glossary():
    """术语表 —— 与前端 data/glossary.ts 的 key 集合一致。

    AI 回答里出现的术语名与界面上的写法必须同源，否则同一个概念
    会在两个地方叫两个名字。
    """
    return {"count": len(TERMS), "terms": list(TERMS)}
