# ==============================================================================
# 文件路径: wordcrafter/webui.py
# Web UI —— 「本地计算 + Web 同步」HTML 前端 + 完整 JSON 后端
#   - 纯 stdlib http.server，无第三方依赖；共享 GUI 仓储实例（进程内同步）+ 磁盘持久化
#   - 默认 0.0.0.0:8765，访问需 token（URL ?token=…，前端全链路自动携带）
#   后端接口：总览 / 学习会话+评分 / 生词库(列表/删除) / 词典 / 学习计划(列表/切换/新建)
#            / 本地词典仓文件 / 历史(列表/详情/导出下载/删除)
# ==============================================================================
import html as _html
import json
import socket
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def lan_addresses():
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip:
                ips.append(ip)
        except Exception:
            pass
    return ips


_INDEX_HTML = r"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>WordCrafter Web</title><style>
:root{--bg:#F7F7F8;--card:#fff;--txt:#18181B;--mut:#8E8E98;--acc:#4F46E5;
--acc2:#EEF2FF;--bdr:#E4E4E7;--ok:#16A34A;--err:#DC2626;--danger:#DC2626}
@media(prefers-color-scheme:dark){:root{--bg:#171717;--card:#1F1F22;--txt:#F4F4F5;
--mut:#8E8E98;--acc:#818CF8;--acc2:#262A40;--bdr:#323236}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei UI",sans-serif}
header{position:sticky;top:0;z-index:9;background:color-mix(in srgb,var(--bg) 90%,transparent);
backdrop-filter:blur(10px);border-bottom:1px solid var(--bdr)}
nav{display:flex;gap:2px;padding:8px 8px;overflow-x:auto;white-space:nowrap}
nav button{border:none;background:transparent;color:var(--mut);padding:9px 13px;
border-radius:999px;font-size:15px;cursor:pointer}
nav button.on{background:var(--acc2);color:var(--acc);font-weight:700}
main{padding:12px;max-width:920px;margin:0 auto;padding-bottom:40px}
.card{background:var(--card);border:1px solid var(--bdr);border-radius:16px;
padding:15px;margin-bottom:11px}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.chip{background:var(--card);border:1px solid var(--bdr);border-radius:14px;
padding:11px 12px;flex:1;min-width:100px;text-align:center}
.chip b{display:block;font-size:23px;color:var(--acc)}
h1{font-size:19px;margin:6px 0} h2{font-size:16px;margin:8px 0 4px}
.mut{color:var(--mut);font-size:13px}
input,textarea,select{width:100%;padding:10px 11px;border-radius:10px;border:1px solid var(--bdr);
background:var(--card);color:var(--txt);font-size:15px;margin:4px 0;font-family:inherit}
button.act{border:none;border-radius:10px;padding:11px 15px;font-size:15px;cursor:pointer;
background:var(--acc);color:#fff;font-weight:600}
button.sec{background:var(--card);color:var(--txt);border:1px solid var(--bdr);border-radius:10px;
padding:10px 14px;font-size:14px;cursor:pointer}
button.ghost{background:transparent;color:var(--mut);border:none;font-size:13px;cursor:pointer}
.bigword{font-size:30px;font-weight:800}
.lbl{color:var(--acc);font-weight:700;margin-top:10px}
ul{list-style:none;margin:0;padding:0}li{padding:9px 2px;border-bottom:1px solid var(--bdr)}
li:last-child{border-bottom:none}
.lirow{display:flex;gap:8px;align-items:flex-start}
.lirow .main{flex:1;min-width:0}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;
background:var(--acc2);color:var(--acc);margin-left:6px}
.ok{color:var(--ok)}.err{color:var(--err)}
.hide{display:none}
#toast{position:fixed;bottom:14px;left:50%;transform:translateX(-50%);z-index:99;
background:var(--card);border:1px solid var(--bdr);border-radius:12px;padding:10px 16px;
display:none;font-size:14px;max-width:90vw}
</style></head><body>
<header><nav id="nav">
<button data-p="overview" class="on">总览</button>
<button data-p="study">学习</button>
<button data-p="plans">学习计划</button>
<button data-p="vocab">生词库</button>
<button data-p="lookup">词典</button>
<button data-p="history">历史</button>
</nav></header>
<main>
<section id="p-overview" class="page"></section>
<section id="p-study" class="page" hidden></section>
<section id="p-plans" class="page" hidden></section>
<section id="p-vocab" class="page" hidden></section>
<section id="p-lookup" class="page" hidden></section>
<section id="p-history" class="page" hidden></section>
</main>
<div id="toast"></div>
<script>
const QTOKEN = new URLSearchParams(location.search).get('token') || '';
let TOKEN = QTOKEN;
try{if(QTOKEN){document.cookie='wc_token='+encodeURIComponent(QTOKEN)+'; path=/; max-age=31536000'}}catch(e){}
(function(){const m=document.cookie.match(/(?:^|; )wc_token=([^;]+)/);if(m&&m[1]&&!TOKEN){TOKEN=decodeURIComponent(m[1])}})();
window.addEventListener('error',function(e){try{const d=document.createElement('div');d.style.cssText='position:fixed;top:8px;left:50%;transform:translateX(-50%);background:#FEE2E2;color:#B91C1C;border-radius:10px;padding:8px 14px;z-index:999;max-width:92vw;font-size:13px';d.textContent='JS 错误：'+(e.message||'unknown');document.body.appendChild(d);setTimeout(()=>d.remove(),6000)}catch(_){}});
function api(path){const sep=path.indexOf('?')>=0?'&':'?';return path+(TOKEN?sep+'token='+encodeURIComponent(TOKEN):'')}
async function Q(p,o){o=o||{};const r=await fetch(api(p),{method:o.m||'GET',
 headers:{'Content-Type':'application/json','X-Token':TOKEN},
 body:o.b?JSON.stringify(o.b):undefined});let d;try{d=await r.json()}catch(e){d=null}
 if(!r.ok){throw new Error((d&&d.error)||('HTTP '+r.status))}return d}
function esc(s){const d=document.createElement('div');d.textContent=s==null?'':String(s);return d.innerHTML}
let toastTimer;
function toast(t,isErr){const x=document.getElementById('toast');x.textContent=t;
 x.style.display='block';x.style.color=isErr?'var(--err)':'var(--txt)';
 clearTimeout(toastTimer);toastTimer=setTimeout(()=>x.style.display='none',2400)}
function spin(){return '<div class="mut">加载中…</div>'}
const pages={overview:loadOverview,study:()=>loadStudy('auto'),plans:loadPlans,
 vocab:loadVocab,lookup:loadLookup,history:loadHistory};
function go(p){document.querySelectorAll('.page').forEach(x=>x.hidden=true);
 const sec=document.getElementById('p-'+p);sec.hidden=false;
 document.querySelectorAll('#nav button').forEach(b=>b.classList.toggle('on',b.dataset.p===p));
 if(pages[p])pages[p]()}
document.getElementById('nav').addEventListener('click',e=>{const b=e.target.closest('button');if(b)go(b.dataset.p)});
async function loadOverview(){const p=document.getElementById('p-overview');p.innerHTML=spin();
 try{const s=await Q('/api/summary');
 p.innerHTML='';p.appendChild(el('h1','','今日学习'));
 const c=el('div','row');
 [['新词',s.new],['待复习',s.due],['今日完成',s.done_today],['已掌握',s.mastered]].forEach(([k,v])=>{const d=el('div','chip');d.appendChild(el('b','',v));d.appendChild(el('div','',k));c.appendChild(d)});
 p.appendChild(c);
 const card=el('div','card');card.appendChild(el('div','','当前计划：'+(s.plan||'（未创建，默认生词库）')));
 card.appendChild(el('div','mut','词库 '+s.vocab_total+' 词 · 今日学习 '+s.total+' 次'));
 const b=el('button','act','开始今日学习');b.onclick=()=>{go('study');loadStudy('auto')};card.appendChild(b);
 p.appendChild(card);
 const d2=el('div','card');d2.innerHTML='<div class="lbl">今日学习记录</div><div class="mut">'+
  '学习 '+s.total+' · 新词 '+s.new+' · 复习 '+s.review+' · 忘记 '+s.forget+' · 困难 '+s.hard+
  ' · 一般 '+s.good+' · 简单 '+s.easy+'</div>';p.appendChild(d2);
 }catch(e){p.innerHTML='';p.appendChild(el('div','err','加载失败：'+esc(e.message)));}}
function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;
 if(text!=null)e.textContent=text;return e}
let session={words:[],pos:0,revealed:false,extra:[]};
async function loadStudy(mode){const p=document.getElementById('p-study');p.innerHTML=spin();
 try{const s=await Q('/api/study/session?mode='+encodeURIComponent(mode||'auto'));
  session.words=s.queue||[];session.pos=0;session.revealed=false;
  p.innerHTML='';p.appendChild(el('h1','','学习 · '+(s.due_msg||'开始')));
  const row=el('div','row');const b1=el('button','sec','开始复习');b1.onclick=()=>loadStudy('review');
  const b2=el('button','sec','学新词');b2.disabled=!!(s.due&&s.due>0);
  b2.textContent=(s.due&&s.due>0)?'先完成复习':((s.fresh&&s.fresh>0)?'学新词 ('+s.fresh+')':'学新词');
  b2.onclick=()=>loadStudy('new');row.appendChild(b1);row.appendChild(b2);
  p.appendChild(row);renderWord(p);
 }catch(e){p.innerHTML='';p.appendChild(el('div','err','加载失败：'+esc(e.message)));}}
function renderWord(p){const parts=p.querySelectorAll('.card.extra');parts.forEach(x=>x.remove());
 if(session.pos>=session.words.length){const card=el('div','card');card.appendChild(el('h1','','🎉 本轮完成'));
  card.appendChild(el('div','mut','可返回总览，或开始复习/学新词'));p.appendChild(card);return}
 const w=session.words[session.pos];
 const card=el('div','card');card.appendChild(el('div','mut','第 '+(session.pos+1)+' / '+session.words.length+' 词'));
 card.appendChild(el('div','bigword',w.word));
 const ph=el('div','mut');ph.id='phon';card.appendChild(ph);
 const ans=el('div','mut');ans.id='ans';ans.style.whiteSpace='pre-wrap';ans.style.marginTop='10px';card.appendChild(ans);
 const b=el('button','act','显示答案');b.id='revealBtn';b.onclick=reveal;card.appendChild(b);
 p.appendChild(card);
 const rr=el('div','row');rr.id='ratings';rr.hidden=true;card.appendChild(rr);
 [['forget','忘记'],['hard','困难'],['good','一般'],['easy','简单']].forEach(([k,t])=>{
  const x=el('button',k==='forget'?'sec':'act',t);x.style.flex='1';x.onclick=()=>rate(k);rr.appendChild(x)});
 Q('/api/lookup?word='+encodeURIComponent(w.word)).then(d=>{if(d.phonetic)ph.textContent=d.phonetic;
  if(d.pos_def&&d.pos_def.indexOf('未找到')<0)ans.textContent='【释义】\n'+d.pos_def+(d.example?'\n\n【例句】\n'+d.example:'');}).catch(()=>{})}
function reveal(){const r=document.getElementById('ratings');if(r)r.hidden=false;
 const b=document.getElementById('revealBtn');if(b)b.remove();session.revealed=true}
async function rate(k){const w=session.words[session.pos].word;try{await Q('/api/study/review',
 {m:'POST',b:{word:w,rating:k}})}catch(e){toast('保存失败：'+e.message,true)}session.pos+=1;
 session.revealed=false;renderWord(document.getElementById('p-study'))}
async function loadPlans(){const p=document.getElementById('p-plans');p.innerHTML=spin();
 try{const d=await Q('/api/decks');
  p.innerHTML='';p.appendChild(el('h1','','学习计划'));
  const ul=el('ul');p.appendChild(ul);
  (d.decks||[]).forEach(x=>{const li=el('li');li.innerHTML='<div class="lirow"><div class="main"><b>'
   +(x.is_active?'● ':'○ ')+esc(x.name)+'</b><span class="badge">'+esc(x.source_label||'')+
   '</span><div class="mut">'+x.word_count+' 词 · 已掌握 '+x.mastered+'</div></div>';
   if(!x.is_active){const b=el('button','sec','设为当前');b.onclick=async()=>{await Q('/api/decks/switch',{m:'POST',b:{id:x.id}});toast('已切换');loadPlans()};li.querySelector('.main').appendChild(b)}
   const del=el('button','ghost','删除');del.onclick=async()=>{if(!confirm('删除计划「'+x.name+'」？'))return;await Q('/api/decks/delete',{m:'POST',b:{id:x.id}});loadPlans()};
   li.appendChild(del);ul.appendChild(li)});
  p.appendChild(el('h2','','＋ 新建学习计划'));
  const card=el('div','card');p.appendChild(card);
  card.appendChild(labeled('名称',inp('name','计划名称')));
  const src=el('select','');src.innerHTML='<option value="vocab">生词库</option><option value="custom">自定义单词</option><option value="local_dict">本地词典/词书</option>';card.appendChild(labeled('来源',src));
  const custom=el('textarea','');custom.placeholder='自定义：每行一个或逗号分隔单词';custom.hidden=true;custom.id='customWords';card.appendChild(custom);
  const filesBox=el('select','');filesBox.hidden=true;filesBox.id='storeFiles';card.appendChild(filesBox);
  src.onchange=()=>{custom.hidden=src.value!=='custom';filesBox.hidden=src.value!=='local_dict';
   if(src.value==='local_dict')fillFiles()};
  const b=el('button','act','创建');b.onclick=async()=>{const name=document.getElementById('deckName').value.trim();
   let words=null,file=null;if(src.value==='custom'){words=(document.getElementById('customWords').value||'').split(/[,，\s]+/).map(s=>s.trim()).filter(Boolean)}
   if(src.value==='local_dict')file=filesBox.value;
   if(!name){toast('请输入名称',true);return}
   await Q('/api/decks/create',{m:'POST',b:{name:name,source:src.value,words:words,file:file}});
   toast('已创建');loadPlans()};card.appendChild(b);
 }catch(e){p.innerHTML='';p.appendChild(el('div','err','加载失败：'+esc(e.message)));}}
async function fillFiles(){try{const d=await Q('/api/store/files');const s=document.getElementById('storeFiles');
 s.innerHTML=''; (d.files||[]).forEach(f=>{const o=el('option','');o.value=f.filename;o.textContent=f.label+'（'+f.count+' 词）';s.appendChild(o)})}catch(e){}}
function labeled(t,w){const w2=el('div','');const l=el('div','mut',t);l.style.marginTop='8px';w2.appendChild(l);w2.appendChild(w);return w2}
function inp(id,ph){const i=el('input','');i.id=id;i.placeholder=ph||'';return i}
async function loadVocab(){const p=document.getElementById('p-vocab');p.innerHTML=spin();
 try{const d=await Q('/api/vocab');
  p.innerHTML='';p.appendChild(el('h1','','生词库 · '+d.total+' 词'));
  const inp=el('input','');inp.placeholder='🔍 搜索…';inp.oninput=()=>{clearTimeout(window.__vt);window.__vt=setTimeout(loadVocab,250)};p.appendChild(inp);
  const ul=el('ul');p.appendChild(ul);
  (d.words||[]).forEach(w=>{const li=el('li');li.innerHTML='<div class="lirow"><div class="main"><b>'+esc(w.word)+'</b> <span class="mut">'+esc(w.phonetic||'')+'</span><br><span class="mut">'+esc(w.meaning||'（暂无本地释义，可到词典查询）')+'</span></div>';
   const del=el('button','ghost','✕');del.onclick=async()=>{await Q('/api/vocab/delete',{m:'POST',b:{word:w.word}});toast('已删除');li.remove()};
   li.appendChild(del);ul.appendChild(li)});
 }catch(e){p.innerHTML='';p.appendChild(el('div','err','加载失败：'+esc(e.message)));}}
async function loadLookup(){const p=document.getElementById('p-lookup');
 if(!p.dataset.built){p.innerHTML='';p.appendChild(el('h1','','词典查询'));
  const inp=el('input','');inp.placeholder='输入英文单词…';inp.id='lk';p.appendChild(inp);
  const b=el('button','act','查询');p.appendChild(b);
  const out=el('div','card');out.id='lkout';p.appendChild(out);
  const doq=async()=>{const w=document.getElementById('lk').value.trim();if(!w)return;
   out.innerHTML=spin();try{const d=await Q('/api/lookup?word='+encodeURIComponent(w));
    out.innerHTML='<div class="bigword">'+esc(w)+'</div>'+(d.phonetic?'<div class="mut">'+esc(d.phonetic)+'</div>':'')+
    '<div class="lbl">释义</div><div style="white-space:pre-wrap">'+esc(d.pos_def||'未找到释义')+'</div>'+
    (d.example?'<div class="lbl">例句</div><div style="white-space:pre-wrap">'+esc(d.example)+'</div>':'')+
    (d.source?'<div class="mut">来源：'+esc(d.source)+'</div>':'')}catch(e){out.innerHTML='<div class="err">'+esc(e.message)+'</div>'}};
  b.onclick=doq;inp.onkeydown=e=>{if(e.key==='Enter')doq()};p.dataset.built='1';}}
async function loadHistory(){const p=document.getElementById('p-history');p.innerHTML=spin();
 try{const d=await Q('/api/history');
  p.innerHTML='';p.appendChild(el('h1','','生成历史 · '+d.total));
  const ul=el('ul');p.appendChild(ul);
  (d.items||[]).forEach(it=>{const li=el('li');
   li.innerHTML='<div class="lirow"><div class="main"><b>'+esc(it.icon)+' '+esc(it.title)+'</b> <span class="mut">'+esc(it.time)+'</span>';
   const row2=el('div','row');
   const v=el('button','ghost','查看');v.onclick=async()=>{try{const f=await Q('/api/history?id='+it.id);renderHistory(f,li)}catch(e){toast(e.message,true)}};row2.appendChild(v);
   const ex=el('button','ghost','下载TXT');ex.onclick=()=>{location.href=api('/api/history/export?id='+it.id+'&fmt=txt')};row2.appendChild(ex);
   const exm=el('button','ghost','下载MD');exm.onclick=()=>{location.href=api('/api/history/export?id='+it.id+'&fmt=md')};row2.appendChild(exm);
   const del=el('button','ghost','删除');del.onclick=async()=>{if(!confirm('确认删除？'))return;await Q('/api/history/delete',{m:'POST',b:{id:it.id}});toast('已删除');loadHistory()};row2.appendChild(del);
   li.appendChild(row2);ul.appendChild(li)});
 }catch(e){p.innerHTML='';p.appendChild(el('div','err','加载失败：'+esc(e.message)));}}
function renderHistory(f,li){const box=el('div','card');
 box.innerHTML='<div class="lbl">英文</div><div style="white-space:pre-wrap;font-size:15px">'+esc(f.en||'(空)')+'</div><div class="lbl">中文</div><div style="white-space:pre-wrap;color:var(--mut)">'+esc(f.zh||'')+'</div>';
 li.appendChild(box)}
go('overview');
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    server_version = "WordCrafterWeb/2.0"

    def _send(self, code, obj, content_type="application/json", headers=None):
        if isinstance(obj, (dict, list)):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        elif isinstance(obj, str):
            body = obj.encode("utf-8")
        else:
            body = obj or b""
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _ok(self, obj, content_type="application/json", headers=None):
        self._send(200, obj, content_type=content_type, headers=headers)

    def _bad(self, msg):
        self._send(400, {"error": msg})

    def _token_ok(self):
        token = self.server.token
        if not token:
            return True
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if params.get("token", [""])[0] == token:
            return True
        if self.headers.get("X-Token") == token:
            return True
        cookie = self.headers.get("Cookie", "")
        if f"wc_token={token}" in cookie.replace(" ", ""):
            return True
        return False

    def log_message(self, *args):
        pass

    def do_GET(self):
        if not self._token_ok():
            self._send(401, {"error": "token 无效"})
            return
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        st = self.server.state
        if route in ("/", "/index.html"):
            self._ok(_INDEX_HTML, content_type="text/html")
            return
        if route == "/api/summary":
            words = st.vocab_history()
            stats = st.study.stats(words)
            day = st.logs.get_day()
            self._ok({"vocab_total": len(words), **stats,
                      "plan": (st.decks.active() or {}).get("name"),
                      **{k: day.get(k, 0) for k in ("total", "new", "review",
                                                    "forget", "hard", "good", "easy")}})
            return
        if route == "/api/vocab":
            q = (qs.get("q", [""])[0] or "").lower()
            words = st.vocab_history()
            if q:
                words = [w for w in words if q in w]
            out = []
            for w in words[:500]:
                cache = st.cfg.vocab_repo.cache.get(w)
                out.append({"word": w,
                            "phonetic": (cache or {}).get("phonetic", ""),
                            "meaning": (cache or {}).get("pos_def", "").replace("\n", " · ")[:200]})
            self._ok({"total": len(words), "words": out})
            return
        if route == "/api/lookup":
            word = (qs.get("word", [""])[0] or "").strip()
            if not word:
                self._bad("缺少 word")
                return
            try:
                entry = st.lookup(word)
            except Exception as exc:
                self._bad(str(exc))
                return
            self._ok(entry or {"pos_def": "未找到释义", "source": ""})
            return
        if route == "/api/store/files":
            self._ok({"files": st.store_files()})
            return
        if route == "/api/decks":
            self._ok({"decks": st.deck_list()})
            return
        if route == "/api/history":
            sid = qs.get("id", [None])[0]
            if sid:
                s = st.sessions.get(sid)
                if not s:
                    self._bad("不存在")
                    return
                content = s.get("content") or {}
                self._ok({"en": content.get("en", ""), "zh": content.get("zh", ""),
                          "title": s.get("title", "")})
                return
            self._ok({"total": len(st.sessions.sessions),
                      "items": st.history_items()})
            return
        if route == "/api/history/export":
            sid = qs.get("id", [""])[0]
            fmt = qs.get("fmt", ["txt"])[0]
            s = st.sessions.get(sid)
            if not s:
                self._bad("不存在")
                return
            import io
            text = st.export_text(sid, fmt)
            fname = s.get("id", "history") + (".md" if fmt == "md" else ".txt")
            self._ok(text, content_type="text/plain",
                     headers={"Content-Disposition": f'attachment; filename="{fname}"'})
            return
        if route == "/api/study/session":
            mode = qs.get("mode", ["auto"])[0]
            due = [w for w in st.deck_words() if st.is_due(w)]
            fresh = [w for w in st.deck_words() if st.is_new(w)]
            if mode == "review":
                queue = due
            elif mode == "new":
                queue = [] if due else fresh[:st.daily_new()]
            else:
                queue = due or fresh[:st.daily_new()]
            self._ok({"queue": [{"word": w} for w in queue], "due": len(due),
                      "fresh": len(fresh),
                      "due_msg": (f"待复习 {len(due)} · 先完成复习" if due
                                  else f"新词 {len(fresh)} · 复习已完成")})
            return
        self._bad("未找到接口 " + route)

    def do_POST(self):
        if not self._token_ok():
            self._send(401, {"error": "token 无效"})
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            data = json.loads(raw or "{}")
        except Exception:
            self._bad("请求体不是 JSON")
            return
        route = urllib.parse.urlparse(self.path).path
        st = self.server.state
        with st.lock:
            if route == "/api/study/review":
                word = str(data.get("word", "")).strip().lower()
                rating = data.get("rating")
                if not word or rating not in ("forget", "hard", "good", "easy"):
                    self._bad("参数不完整")
                    return
                card = st.study.get(word)
                was_new = card.get("state") == "NEW"
                st.study.record_review(word, rating)
                st.logs.record(time.time(), was_new, rating, word)
                self._ok({"ok": True})
                return
            if route == "/api/vocab/delete":
                word = str(data.get("word", "")).strip().lower()
                if word and word in st.cfg.vocab_history:
                    st.cfg.vocab_repo.remove_word(word)
                    self._ok({"ok": True})
                    return
                self._bad("单词不存在")
                return
            if route == "/api/decks/switch":
                did = data.get("id")
                if st.decks.get(did):
                    st.decks.set_active(did)
                    self._ok({"ok": True})
                    return
                self._bad("计划不存在")
                return
            if route == "/api/decks/delete":
                did = data.get("id")
                st.decks.delete(did)
                self._ok({"ok": True})
                return
            if route == "/api/decks/create":
                name = str(data.get("name", "")).strip() or "新计划"
                source = data.get("source", "vocab")
                words = data.get("words") or None
                file = data.get("file")
                if source == "custom" and (not words or len(words) == 0):
                    self._bad("自定义来源需至少一个单词")
                    return
                if source == "local_dict" and not file:
                    self._bad("请选择本地词典/词书")
                    return
                deck = st.decks.create(name, source, source_id=file, words=words)
                st.decks.set_active(deck["id"])
                self._ok({"ok": True})
                return
            if route == "/api/history/delete":
                sid = data.get("id")
                st.sessions.delete(sid)
                self._ok({"ok": True})
                return
        self._bad("未找到接口 " + route)


class WebState:
    """Web 后端数据适配器（共享 GUI 仓储实例，进程内同步 + 磁盘持久化）。"""

    def __init__(self, cfg, study, decks, logs, sessions):
        self.cfg = cfg
        self.study = study
        self.decks = decks
        self.logs = logs
        self.sessions = sessions
        self.lock = threading.Lock()

    def vocab_history(self):
        return list(self.cfg.vocab_history)

    def deck_words(self):
        words = self.decks.word_set(self.decks.active(), self.cfg)
        return words if words else self.vocab_history()

    def daily_new(self):
        try:
            return int(self.cfg.config_repo.data.get("daily_new_words", 10) or 10)
        except Exception:
            return 10

    def is_new(self, w):
        return self.study.get(w).get("state") == "NEW"

    def is_due(self, w):
        c = self.study.get(w)
        return (c.get("state") not in ("NEW", "MASTERED")
                and c.get("next_review", 0) <= time.time())

    def store_files(self):
        return self.cfg.dictionary_store.list_files()

    def deck_list(self):
        out = []
        for d in self.decks.decks:
            words = self.decks.word_set(d, self.cfg)
            mastered = sum(1 for w in words
                           if self.study.get(w).get("state") == "MASTERED")
            labels = {"vocab": "生词库", "custom": "自定义", "local_dict": "本地词典/词书"}
            out.append({"id": d.get("id"), "name": d.get("name"),
                        "source_label": labels.get(d.get("source_type"), ""),
                        "word_count": len(words), "mastered": mastered,
                        "is_active": bool(d.get("is_active"))})
        return out

    def history_items(self):
        icon = {"vocab": "📝", "study": "🧠", "reading": "📖", "acg": "🎬", "dictionary": "📚"}
        items = []
        for s in self.sessions.sessions[:120]:
            items.append({"id": s.get("id"), "kind": s.get("kind"),
                          "icon": icon.get(s.get("kind"), "•"),
                          "title": s.get("title", ""),
                          "time": time.strftime("%m-%d %H:%M",
                                                time.localtime(s.get("created_at", 0)))})
        return items

    def export_text(self, sid, fmt="txt"):
        import io
        buf = io.StringIO()
        s = self.sessions.get(sid)
        if not s:
            return ""
        content = s.get("content") or {}
        en = (content.get("en") or "").strip()
        zh = (content.get("zh") or "").strip()
        title = s.get("title", "")
        if fmt == "md":
            buf.write(f"# {title}\n\n")
            if en:
                buf.write("## English\n\n" + en + "\n\n")
            if zh:
                buf.write("## Chinese\n\n" + zh + "\n")
        else:
            buf.write(f"=== {title} ===\n\n")
            if en:
                buf.write(en + "\n\n")
            if zh:
                buf.write("=== Chinese ===\n\n" + zh + "\n")
        return buf.getvalue()

    def lookup(self, word):
        from .services.definitions import DictionaryService
        entry, layer = DictionaryService.lookup_sync(word, self.cfg)
        if not entry:
            return {"pos_def": "未找到释义", "source": ""}
        if layer == "online":
            try:
                self.cfg.vocab_repo.cache[entry.get("word", word)] = entry
                self.cfg.vocab_repo.save_cache()
            except Exception:
                pass
        entry["source"] = entry.get("source") or layer
        return entry


class WebServer:
    """局域网 Web UI 服务。"""

    def __init__(self, state, port=8765, token=""):
        self.state = state
        self.port = int(port)
        self.token = token
        self._httpd = None
        self._thread = None

    def start(self):
        if self._httpd:
            return False
        self._httpd = ThreadingHTTPServer(("0.0.0.0", int(self.port)), _Handler)
        if int(self.port) == 0:
            self.port = self._httpd.server_address[1]
        self._httpd.token = self.token
        self._httpd.state = self.state
        self._thread = threading.Thread(target=self._httpd.serve_forever,
                                        daemon=True)
        self._thread.start()
        return True

    def stop(self):
        if self._httpd:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            except Exception:
                pass
            self._httpd = None
            self._thread = None

    def is_running(self):
        return self._httpd is not None

    @property
    def urls(self):
        base = f"http://{{ip}}:{self.port}"
        tail = f"?token={self.token}" if self.token else ""
        return [base.format(ip=ip) + tail for ip in lan_addresses()] + \
               [f"http://127.0.0.1:{self.port}" + tail]
