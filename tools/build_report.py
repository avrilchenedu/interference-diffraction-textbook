"""Generate the project report (Markdown) from content.json, so the report and
the website share exactly the same verbatim text.

usage: python3 -I build_report.py <site dir> <out.md>
"""
import json
import os
import sys

SITE, OUT = sys.argv[1], sys.argv[2]
D = json.load(open(os.path.join(SITE, 'content.json'), encoding='utf-8'))
PAGES = {p['id']: p for p in D['pages']}
SRC = D['sources']
SIMNAME = {'superposition': '波的疊加（兩個脈衝相遇）', 'ripple': '水波干涉（兩個同相點波源）', 'doubleslit': '雙狹縫干涉', 'singleslit': '單狹縫繞射', 'thinfilm': '薄膜干涉'}
L = []


def esc(s):
    return str(s).replace('|', '｜').replace('*', '＊')


def cell(s):
    return esc(s).replace('\n', '<br>')


def para(s):
    for line in str(s).split('\n'):
        L.append(esc(line) + '\\')
    if L[-1].endswith('\\'):
        L[-1] = L[-1][:-1]
    L.append('')


def tbl(head, rows):
    L.append('| ' + ' | '.join(cell(h) for h in head) + ' |')
    L.append('|' + '---|' * len(head))
    for r in rows:
        L.append('| ' + ' | '.join(cell(c) for c in r) + ' |')
    L.append('')


def block(b, lvl):
    t = b['t']
    if t == 'h':
        L.append('#' * lvl + ' ' + b['title'])
        L.append('')
    elif t == 'paras':
        for p in b['paras']:
            para(p)
    elif t == 'note':
        L.append('**⚠ ' + esc(b['note']) + '**')
        L.append('')
    elif t == 'box':
        L.append(f'**【{esc(b["title"])}】**')
        L.append('')
        para(b['text'])
    elif t == 'kv':
        tbl(['欄位', '內容'], [[r['label'], r['text']] for r in b['rows']])
    elif t == 'table':
        tbl(b['head'], b['rows'])
    elif t == 'linktable':
        tbl(b['head'] + ['網址'], [r['cells'] + [r['link'] or ''] for r in b['rows']])
    elif t == 'media':
        cap = '　'.join(x for x in [b.get('kind', '') if not str(b.get('kind', '')).startswith('0') else '',
                                    b.get('text', '')] if x).replace('\n', ' ')
        if b.get('missing'):
            L.append(f'> ⚠ 圖檔待補：`{b["file"]}`　{esc(cap)}')
            L.append('')
        else:
            imgs = b.get('imgs') or [{'src': b['src'], 'link': b.get('link')}]
            w = '4.5in' if len(imgs) == 1 else '2.9in'
            for im in imgs:
                L.append(f'![{esc(cap) or "圖"}]({im["src"]}){{width={w}}}')
                L.append('')
            for im in imgs:
                if im.get('attrib'):
                    L.append(f'網路替代圖：{esc(im["attrib"])}　{im["link"]}')
                elif im.get('credit'):
                    L.append(f'{esc(im["credit"])}　{im["link"]}')
                elif im.get('link'):
                    L.append(f'{esc(b.get("credit", "")).replace(chr(10), " ")}　{im["link"]}')
                L.append('')
            if b.get('web'):
                L.append(f'（原規劃圖檔：`{b["file"]}`）')
                L.append('')
    elif t == 'sim':
        L.append(f'> 🔬 互動模擬：{SIMNAME[b["sim"]]}（網站內嵌，可操作）' + (f'　{esc(b["text"])}' if b.get('text') else ''))
        L.append('')
    elif t == 'link':
        L.append(f'→ 網站連結：{b["title"]}（{PAGES[b["target"]]["nav"]}）')
        L.append('')
    elif t == 'exam':
        L.append('> 試題評量：本次不做，網站保留入口位置。')
        L.append('')
    elif t == 'ref':
        for p in b['paras']:
            para(p)
        L.append(b['link'])
        L.append('')
    elif t == 'quote':
        L.append('> ' + esc(b['text']).replace('\n', '\\\n> '))
        L.append('>')
        L.append(f'> （出處：{esc(b["source"])}）')
        L.append('')
    elif t == 'activity':
        L.append(f'**{esc(b["title"])}**')
        L.append('')
        if b['situation']:
            para(b['situation'])
        L.append('使用材料與操作：')
        L.append('')
        para(b['material'])
        for q in b['questions']:
            para(q)
    elif t == 'tans':
        L.append(f'**{esc(b["title"])}**')
        L.append('')
        tbl(['欄位', '內容'], [['使用材料與操作', b['material']], ['參考答案與判讀', b['answer']],
                             ['常見錯誤與引導', b['guide']]])
    elif t == 'card':
        L.append(f'**{esc(b["title"])}**（{"／".join(m.replace(chr(10), " ") for m in b["meta"])}）')
        L.append('')
        tbl(['欄位', '內容'], [[r['label'], r['text']] for r in b['rows']])
        if b.get('foot'):
            para(b['foot'])
    elif t == 'guide':
        L.append(f'**{esc(b["title"])}**')
        L.append('')
        tbl(['欄位', '內容'], [list(x) for x in b['kv']])
        tbl(b['head'], b['rows'])
    elif t == 'shot':
        L.append(f'![{esc(b["cells"][0]).replace(chr(10), " ")}]({b["src"]}){{width=2.6in}}')
        L.append('')
        tbl(['欄位', '內容'], [[h, c] for h, c in zip(b['head'], b['cells'])])
    elif t == 'credits':
        tbl(['圖檔', '用途（07A）', '作者／授權', '來源頁'],
            [[m['file'].split('/')[-1], m['text'], ('網路替代圖：' + m['attrib']) if m.get('attrib') else m['credit'], m['link']] for m in b['items']])

def page(pid, lvl=2):
    p = PAGES[pid]
    L.append('#' * lvl + ' ' + p['title'])
    L.append('')
    for b in p['blocks']:
        block(b, lvl + 1)



def deck(pid):
    p = PAGES[pid]
    L.append('## ' + p['nav'] + '　' + p['title'])
    L.append('')
    for i, sl in enumerate(p['deck']):
        if sl.get('kind') == 'title':
            L.append(f'### 投影片 {i + 1}　節次說明（{sl["time"]}）')
            L.append('')
            tbl(['欄位', '內容'], [[c['label'], c['text']] for c in sl['kv']])
            continue
        L.append(f'### 投影片 {i + 1}　{sl["heading"]}（{sl["time"]}）')
        L.append('')
        rows_ = [['教師提問', sl['ask']], ['教師活動', sl['do']], ['學生活動與預期表現', sl['student']],
                 ['評量／證據', sl['evidence']], ['教材／備註', sl['material']]]
        if sl.get('text'):
            rows_.append([sl['text']['ref'], '\n'.join(sl['text']['paras'])])
        if sl.get('sim'):
            rows_.append(['互動元件', SIMNAME[sl['sim']]])
        ims = (sl.get('images') or []) + ([sl['reveal']] if sl.get('reveal') else [])
        if ims:
            rows_.append(['圖片', '\n'.join((im.get('cap') or '') + '：' + (im.get('attrib') or im.get('credit') or '') for im in ims)])
        if sl.get('worksheet'):
            rows_.append(['學習單題目', '\n'.join(sl['worksheet'])])
        for c in sl.get('concept', []):
            rows_.append(['概念解釋：' + c['label'], c['text']])
        tbl(['項目', '內容'], [r for r in rows_ if r[1]])
        notes = []
        for g in sl.get('notes', []):
            for lab, v in g['rows']:
                notes.append([g['label'] + ('：' + lab if lab else ''), v])
        if notes:
            L.append('**教師備註**')
            L.append('')
            tbl(['項目', '內容'], notes)


# ------------------------------------------------------------------ front
L += ['---', 'title: 「干涉與繞射」教科書網站　專案報告',
      'subtitle: 四大內容架構整理（教材文本／學習單／AI 指引；試題評量另案）　v3.0',
      'date: 2026-11-27', '---', '']

L += ['# 第一章　專案概述', '',
      '## 製作原則', '',
      '| 項目 | 原則 |', '|---|---|',
      '| 內容依據 | 只以資料夾內 10 份 Word 文件（01–08、10）為依據。 |',
      '| 用字 | 所有教學內容一律逐字取自原文件：原文件用哪個字就用哪個字，不改寫、不替換專有名詞、不最佳化。報告與網站由同一份程式自原文件逐格擷取產生，並以核對程式確認每一段文字都能在原文件中逐字找到。 |',
      '| 欄目標題 | 只有導覽與欄目標題（例如「學習重點」「觀念澄清」「生活中的物理」）為編排用的標籤，不屬於教材內容。 |',
      '| 適用年級 | 高中版（原文件：高中一年級必修物理）。 |',
      '| 缺漏處理 | 原文件沒有的內容一律標示「⚠ 待補」，不自行補寫。 |',
      '| 試題評量 | 本次不做，另有檔案處理；網站保留入口位置。 |',
      '| AI 指引 | 以原文件中的 AI 規範原句彙整為「AI 提問守則」，每句標注出處，不另寫範例。 |',
      '| 圖片 | 原文件列出但未附檔的圖，改用 Wikimedia Commons 上內容相符的開放授權圖片，於圖下標注「網路替代圖」、作者、授權與來源頁。 |',
      '| 互動模擬 | 07A 列出的 4 個模擬檔案未附，網站自行製作 5 個互動模擬（波的疊加依 07B 需求腳本規格）；第 1 節概念比較圖改為互動模擬。模擬介面上的說明文字取自原文件。 |',
      '', '## 網站架構：一個網站、兩種模式', '',
      '教科書模式與教師授課模式放在同一個網站中，以頂端選單切換，由教師自行選擇。', '',
      '| 模式 | 頁面 |', '|---|---|',
      '| 教科書模式 | ' + '、'.join(p['nav'] for p in D['pages'] if p['mode'] == 'book') + ' |',
      '| 教師授課模式 | ' + '、'.join(p['nav'] for p in D['pages'] if p['mode'] == 'teach') + ' |', '']

L += ['# 第二章　來源文件與四大內容對應', '',
      '| 編號 | 文件 | 歸入 |', '|---|---|---|',
      f'| 01 | {SRC["01"]} | 教材文本（教科書第 1–4 節正文、學習重點、觀念澄清、資料來源） |',
      f'| 02 | {SRC["02"]} | 教師授課模式（三節教學流程）；學習單第 1、3 節活動；AI 提問守則部分條文 |',
      f'| 03 | {SRC["03"]} | 學習單第 2 節（學生版）；教師版參考答案與引導 |',
      f'| 04 | {SRC["04"]} | 教材文本：延伸閱讀 |',
      f'| 05 | {SRC["05"]} | 學習單教師用部分：核心教學題目卡 |',
      f'| 06 | {SRC["06"]} | 試題評量（本次不做）；AI 提問守則一條 |',
      f'| 07A | {SRC["07A"]} | 教材文本：圖片與模擬、生活中的物理、圖片授權 |',
      f'| 07B | {SRC["07B"]} | 教師資源：波的疊加需求腳本 |',
      f'| 08 | {SRC["08"]} | AI 指引；教師資源：數位教材整合規劃 |',
      f'| 10 | {SRC["10"]} | 教師授課模式：常見學習困難與引導 |', '']

L += ['# 第三章　教材文本：教科書模式', '']
for pid in ('intro', 'sec1', 'sec2', 'sec3', 'sec4', 'ext'):
    page(pid)
L += ['# 第四章　學習單（學生版）', '']
for pid in ('ws1', 'ws2', 'ws3'):
    page(pid)
L += ['# 第五章　AI 指引：AI 提問守則', '']
page('ai')
L += ['# 第六章　試題評量', '', '本次不做，另有檔案處理。網站在每節末與教師授課模式保留「試題評量」入口。', '']
L += ['# 第七章　教師授課模式', '', '教師授課模式以「上課簡報」為主：每節依 02 教案的時間段落分成數張投影片，每張投影片列出教師提問、對應的課本段落、可點選的互動元件或圖片，以及用來解釋的概念；教師備註可隨時開關。以下先列三節上課簡報，再列教案與資料頁。', '']
for pid in ('d1', 'd2', 'd3'):
    deck(pid)
for pid in ('t_unit', 't1', 't2', 't3', 't_assess', 't_diff'):
    page(pid)
L += ['# 第八章　素材與數位教材規劃', '']
for pid in ('t_media', 't_07b', 't_08', 'credits'):
    page(pid)

L += ['# 第九章　待補與待確認事項', '',
      '## 待補（原始文件未提供）', '',
      '| 序 | 項目 | 文件中提及處 |', '|---|---|---|',
      '| 1 | 第 1 節學習單 Q1–Q8 題目全文 | 02 |',
      '| 2 | 第 3 節學習單題目全文 | 02、10 |',
      '| 3 | 13 頁紙本教科書 | 02 |',
      '| 4 | AI 回應與診斷規範（A01，第 6、8.3、9、10 章） | 08 |',
      '| 5 | 核心教學題目「原始完整版備份」 | 05 |',
      '| 6 | 前測、隨堂測驗、後測題目 | 02、06 |', '',
      '## 待確認', '',
      '| 序 | 事項 | 網站目前處理方式 |', '|---|---|---|',
      '| 1 | 03 基本資料寫「干涉與繞射第3節」，但內容與 02、08 均為第 2 節雙狹縫。 | 放在第 2 節學習單，03 原文照錄。 |',
      '| 2 | 108 課綱高一必修物理只要求定性介紹光的干涉與繞射（PKa-Ⅴc-5、Ⅴc-6）；疊加原理、水波干涉、單狹縫屬選修物理Ⅲ（PKa-Ⅴa）；課綱未見「薄膜」。 | 依原文件標示「高中一年級必修物理」。 |',
      '| 3 | 原文件「相干」與「同調」並用（例：01、03 用相干；02、05 部分用同調）。 | 依指示照原文件用字，不統一。 |',
      '| 4 | 05 寫「七個可評量知識節點」，01 為四個知識節點。 | 教科書依 01 分 4 節；05 七張題目卡依節次放入教師授課模式。 |',
      '| 5 | 01 節點 01 正文末「（可扣課綱代碼）」為填寫提示。 | 不放入正文。 |',
      '| 6 | 07A 的「第1節/繩波_兩種完全重疊比較.png」圖檔不在資料夾。 | 第 1 節改為「波的疊加」互動模擬（依 07B 模擬需求腳本）；07B 附圖保留於教師資源。 |',
      '| 9 | 網路替代圖與原規劃圖的內容不一定完全相同（例：水波 3D 模擬截圖改為實際水槽照片）。 | 每張替代圖都標示原規劃檔名，請確認是否適用。 |',
      '| 7 | 07B 的動畫與模擬、08 的 AI 功能均標明為需求示範、尚未實作。 | 網站只呈現需求文件內容，未實作 AI 對話。 |',
      '| 8 | 04 延伸資源為全單元資源，未分節。 | 放在「延伸閱讀」頁，第 4 節末連結。 |', '']

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('lines', len(L))
