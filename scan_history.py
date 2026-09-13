import json
from db import get_db

def init_history():
    with get_db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS scan_requests (
            id TEXT PRIMARY KEY, created_at TEXT DEFAULT (datetime('now','localtime')),
            finished_at TEXT, mode TEXT, target TEXT, screenshot TEXT, state TEXT,
            kind TEXT, name TEXT, result_id TEXT, message TEXT, response_json TEXT)''')
        columns={r[1] for r in con.execute('PRAGMA table_info(api_usage)')}
        if 'request_id' not in columns:con.execute("ALTER TABLE api_usage ADD COLUMN request_id TEXT DEFAULT ''")

def begin(request_id,mode,target,screenshot):
    with get_db() as con:
        con.execute('INSERT INTO scan_requests(id,mode,target,screenshot,state,message) VALUES(?,?,?,?,?,?)',(request_id,mode,target,screenshot,'processing','Trwa odczyt AI'))

def finish(request_id,state,kind='',name='',result_id='',message='',response=None):
    with get_db() as con:
        con.execute("UPDATE scan_requests SET finished_at=datetime('now','localtime'),state=?,kind=?,name=?,result_id=?,message=?,response_json=? WHERE id=?",(state,kind,name,result_id,message,json.dumps(response or {},ensure_ascii=False),request_id))

def recent(limit=20):
    with get_db() as con:
        from config import PREVIEWS_DIR
        rows=[dict(r) for r in con.execute('SELECT id,created_at,mode,target,state,kind,name,result_id,message,screenshot FROM scan_requests ORDER BY rowid DESC LIMIT ?',(limit,))]
        for row in rows:row['has_preview']=(PREVIEWS_DIR/(row['id']+'.png')).is_file()
        return rows

def calls(page=1):
    with get_db() as con:
        return [dict(r) for r in con.execute('''SELECT a.*,s.state AS final_state,s.target,s.screenshot,s.name AS result_name,s.result_id,s.message AS result_message,s.mode
           FROM api_usage a LEFT JOIN scan_requests s ON s.id=a.request_id
           ORDER BY a.id DESC LIMIT 50 OFFSET ?''',((page-1)*50,))]
