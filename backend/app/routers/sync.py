from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Optional

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])

CRDT_STORE: dict[str, dict] = {}


class MergeRequest(BaseModel):
    collection: str
    id: str
    doc: dict[str, Any]
    node: str


class MergeResponse(BaseModel):
    status: str
    merged_doc: Optional[dict[str, Any]] = None
    conflict: bool = False


def _merge_docs(local: dict, remote: dict) -> tuple[dict, bool]:
    conflict = False
    merged_fields = {}

    local_fields = local.get("fields", {})
    remote_fields = remote.get("fields", {})

    all_keys = set(list(local_fields.keys()) + list(remote_fields.keys()))
    for key in all_keys:
        lf = local_fields.get(key)
        rf = remote_fields.get(key)
        if lf and rf:
            l_hlc = lf.get("hlc", {})
            r_hlc = rf.get("hlc", {})
            l_ts = (l_hlc.get("ts", 0), l_hlc.get("counter", 0), l_hlc.get("node", ""))
            r_ts = (r_hlc.get("ts", 0), r_hlc.get("counter", 0), r_hlc.get("node", ""))
            if l_ts != r_ts:
                conflict = True
            merged_fields[key] = rf if r_ts >= l_ts else lf
        elif rf:
            merged_fields[key] = rf
        else:
            merged_fields[key] = lf

    local_vv = local.get("vv", {})
    remote_vv = remote.get("vv", {})
    merged_vv = {**local_vv}
    for node, ver in remote_vv.items():
        merged_vv[node] = max(merged_vv.get(node, 0), ver)

    l_del = local.get("deleted", False)
    r_del = remote.get("deleted", False)
    deleted = l_del or r_del
    delete_hlc = None
    if deleted:
        l_dhlc = local.get("deleteHLC")
        r_dhlc = remote.get("deleteHLC")
        if l_dhlc and r_dhlc:
            l_t = (l_dhlc.get("ts", 0), l_dhlc.get("counter", 0))
            r_t = (r_dhlc.get("ts", 0), r_dhlc.get("counter", 0))
            delete_hlc = r_dhlc if r_t >= l_t else l_dhlc
        else:
            delete_hlc = r_dhlc or l_dhlc

    return {
        "id": remote.get("id", local.get("id")),
        "fields": merged_fields,
        "vv": merged_vv,
        "deleted": deleted,
        "deleteHLC": delete_hlc,
    }, conflict


@router.post("/merge", response_model=MergeResponse)
def merge_crdt(req: MergeRequest):
    key = f"{req.collection}:{req.id}"
    existing = CRDT_STORE.get(key)

    if existing:
        merged, conflict = _merge_docs(existing, req.doc)
        CRDT_STORE[key] = merged
        if conflict:
            return MergeResponse(status="merged", merged_doc=merged, conflict=True)
        return MergeResponse(status="accepted", conflict=False)

    CRDT_STORE[key] = req.doc
    return MergeResponse(status="accepted", conflict=False)


@router.get("/state/{collection}")
def get_collection_state(collection: str):
    prefix = f"{collection}:"
    docs = {}
    for key, doc in CRDT_STORE.items():
        if key.startswith(prefix):
            doc_id = key[len(prefix):]
            if not doc.get("deleted", False):
                plain = {"id": doc_id}
                for field, reg in doc.get("fields", {}).items():
                    plain[field] = reg.get("value")
                docs[doc_id] = plain
    return {"collection": collection, "documents": docs, "count": len(docs)}
