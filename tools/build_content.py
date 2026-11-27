"""Build content.json for the textbook site from the 10 source .docx files.

Every piece of teaching text is copied directly out of the source documents
(cell by cell); nothing is retyped.  Only navigation labels / section titles
(fields named "label", "title", "nav", "head", "note") are written by hand.

usage: python3 -I build_content.py <folder with the .docx files> <site dir>
"""
import glob
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
SRC_DIR, SITE = sys.argv[1], sys.argv[2]


# ---------------------------------------------------------------- parsing
def ptext(p):
    out = []
    for el in p.iter():
        if el.tag == W + 't':
            out.append(el.text or '')
        elif el.tag == W + 'tab':
            out.append('\t')
        elif el.tag == W + 'br':
            out.append('\n')
    return ''.join(out)


def cell(tc):
    paras = []
    for ch in tc:
        if ch.tag == W + 'p':
            t = ptext(ch).strip()
            if t:
                paras.append(t)
    return paras


def blocks(path):
    root = ET.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
    out = []
    for ch in root.find(W + 'body'):
        if ch.tag == W + 'p':
            t = ptext(ch).strip()
            if t:
                out.append(t)
        elif ch.tag == W + 'tbl':
            out.append([[cell(tc) for tc in tr.findall(W + 'tc')]
                        for tr in ch.findall(W + 'tr')])
    return out


DOC = {}
for f in sorted(glob.glob(os.path.join(SRC_DIR, '[0-9][0-9]*_*.docx'))):  # only the 10 source documents (01–08, 10)
    DOC[os.path.basename(f).split('_')[0]] = blocks(f)
assert sorted(DOC) == ['01', '02', '03', '04', '05', '06', '07A', '07B', '08', '10'], sorted(DOC)
DOCNAME = {
    '01': '核心教材文本開發表', '02': '單元教案與教學指引', '03': '紙本學習單開發表',
    '04': '延伸學習資源教材公版', '05': '核心教學題目', '06': '評量雙向細目表',
    '07A': '多模態輔助教材素材清單', '07B': '多模態輔助教材需求腳本',
    '08': '數位教材整合規劃表', '10': '常見學習困難與引導策略'}


# ---------------------------------------------------------------- full-document parsing (for the 原始文件 pages)
import hashlib
import urllib.parse

R_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
A_BLIP = '{http://schemas.openxmlformats.org/drawingml/2006/main}blip'
_DOCIMG_BY_MD5 = {}
for _f in glob.glob(os.path.join(SITE, 'assets', 'docs', '*.png')):
    _DOCIMG_BY_MD5[hashlib.md5(open(_f, 'rb').read()).hexdigest()] = 'assets/docs/' + os.path.basename(_f)


def raw_blocks(path):
    z = zipfile.ZipFile(path)
    rels = ET.fromstring(z.read('word/_rels/document.xml.rels'))
    rel = {r.get('Id'): r.get('Target') for r in rels}

    def para(p):
        item = {'text': ptext(p).strip()}
        imgs = []
        for el in p.iter():
            if el.tag == A_BLIP:
                tgt = rel.get(el.get(R_NS + 'embed'), '')
                data = z.read('word/' + tgt) if tgt else b''
                src = _DOCIMG_BY_MD5.get(hashlib.md5(data).hexdigest())
                if src:
                    imgs.append(src)
        links = []
        for h in p.iter(W + 'hyperlink'):
            u = rel.get(h.get(R_NS + 'id'))
            if not u:
                continue
            if u.startswith('http'):
                links.append(u)
            elif urllib.parse.unquote(os.path.basename(u)) in PHOTOS:  # 原文件連到本機照片 → 改連網站內同一張照片
                links.append(PHOTO_DIR + urllib.parse.unquote(os.path.basename(u)))
            # 其他連到作者本機資料夾的相對連結無法公開使用，不呈現為連結
        if imgs:
            item['imgs'] = imgs
        if links:
            item['links'] = links
        return item if (item['text'] or imgs) else None

    def rcell(tc):
        out = []
        for ch in tc:
            if ch.tag == W + 'p':
                it = para(ch)
                if it:
                    out.append(it)
            elif ch.tag == W + 'tbl':
                out.append({'table': rtable(ch)})
        return out

    def rtable(tbl):
        return [[rcell(tc) for tc in tr.findall(W + 'tc')] for tr in tbl.findall(W + 'tr')]

    out = []
    for ch in ET.fromstring(z.read('word/document.xml')).find(W + 'body'):
        if ch.tag == W + 'p':
            it = para(ch)
            if it:
                out.append(it)
        elif ch.tag == W + 'tbl':
            out.append({'table': rtable(ch)})
    return out




def C(doc, b, r, c):
    """paragraphs of one table cell, template hints (提示：…) removed"""
    return [p for p in DOC[doc][b][r][c] if not p.startswith('提示：')]


def T(doc, b, r, c):
    return '\n'.join(C(doc, b, r, c))


def P(doc, b):
    return DOC[doc][b]


def rows(doc, b, r0, r1, cols=None):
    out = []
    for r in range(r0, r1):
        row = DOC[doc][b][r]
        idx = cols if cols is not None else range(len(row))
        out.append(['\n'.join(p for p in row[i] if not p.startswith('提示：')) for i in idx])
    return out


def src(*ds):
    return '、'.join(ds)


# ---------------------------------------------------------------- media
PHOTO_DIR = 'assets/photos/'
PHOTOS = {  # filename (as in 07A) -> Wikimedia source page (hyperlinks in 07A)
    '雙狹縫干涉_紅光實拍_Bryan-Tong-Minh_PD.jpg': 'https://commons.wikimedia.org/wiki/File:Subwavelength_slits.JPG',
    '光凳器材組_Waifer-X_Cuesta-College_CC-BY-2.0.jpg': 'https://commons.wikimedia.org/wiki/File:Optical_Bench_educational_Kit_-_Cuesta_College.jpg',
    '光凳實際架設_Cantons-de-lEst_CC-BY-SA-4.0.jpg': 'https://commons.wikimedia.org/wiki/File:Banc_optique_-_exemple_de_montage_01.jpg',
    '單狹縫繞射_藍光雷射_Xyqorophibian_CC-BY-SA-4.0.jpg': 'https://commons.wikimedia.org/wiki/File:Blue_laser_single_slit_diffraction_photo.jpg',
    '可調式單狹縫器_Jan-Krieger_CC-BY-SA-3.0.jpg': 'https://commons.wikimedia.org/wiki/File:Xy_adjustable_optical_slit.jpg',
    '光碟繞射_Hapecko_CC-BY-SA-4.0.jpg': 'https://commons.wikimedia.org/wiki/File:CD_rainbow.jpg',
    '望遠鏡繞射尖峰_ESA-Hubble_CC-BY-4.0.jpg': 'https://commons.wikimedia.org/wiki/File:A_slice_of_Sagittarius.jpg',
    '一般鏡片與抗反射鏡片_Maximilian-Schoenherr_CC0.jpg': 'https://commons.wikimedia.org/wiki/File:Reflective_and_anti-reflective_lens.jpg',
    '水面油膜_gambier20_CC-BY-2.0.jpg': 'https://commons.wikimedia.org/wiki/File:Rainbow_Pollution.jpg',
    '肥皂泡薄膜干涉_Pksois23_CC-BY-SA-4.0.jpg': 'https://commons.wikimedia.org/wiki/File:Thin_Film_Interference_Soap_Bubble.jpg',
    '肥皂膜薄膜干涉_Yaroslav-Ulyushin_CC-BY-4.0.jpg': 'https://commons.wikimedia.org/wiki/File:%D0%98%D0%BD%D1%82%D0%B5%D1%80%D1%84%D0%B5%D1%80%D0%B5%D0%BD%D1%86%D0%B8%D1%8F_%D0%B2_%D1%82%D0%BE%D0%BD%D0%BA%D0%BE%D0%B9_%D0%BC%D1%8B%D0%BB%D1%8C%D0%BD%D0%BE%D0%B9_%D0%BF%D0%BB%D1%91%D0%BD%D0%BA%D0%B5.jpg',
    '牛頓環_Ulfbastel_PD.jpg': 'https://commons.wikimedia.org/wiki/File:Newton_rings.jpg',
    '孔雀羽毛_Bernard-Spragg_CC0.jpg': 'https://commons.wikimedia.org/wiki/File:Peacock_feathers._(20779300743).jpg',
    '藍閃蝶_Alias0591_CC-BY-2.0.jpg': 'https://commons.wikimedia.org/wiki/File:Blue_Morpho_butterfly_(Morpho_peleides)_wings_open.jpg',
}


COMMONS = {c['file']: c for c in json.load(open(os.path.join(SITE, 'assets/commons/commons.json'), encoding='utf-8'))}
# 原文件列出但未附檔的圖 → 網路上找到的替代圖（Wikimedia Commons）
WEB = {
    '封面/干涉與繞射_封面主視覺.png': ['c00.jpg'],
    '封面/封面_紙本13頁.png': ['c01.jpg'],
    '第1節/水波干涉_3D關鍵畫面.png': ['c02.jpg', 'c15.jpg'],
    '第1節/繩波相遇前_自製題圖.png': ['c03.png'],
    '第1節/雙點波源AB點_自製題圖.png': ['c04.png'],
    '惠更斯原理_示意圖解說.png': ['c13.png'],
    '紙本教材用/惠更斯原理_關鍵畫面.png': ['c17.png'],
    '紙本教材用/雙狹縫_亮暗條紋_BD.png': ['c07.png'],
    '雙狹縫實驗架設_空間位置示意.svg': ['c08.jpg'],
    '紙本教材用/雙狹縫實驗架設_空間位置示意.svg.png': ['c08.jpg'],
    '雙狹縫次波模型_自製題圖.png': ['c09.png'],
    '雙狹縫裝置_預測題圖.png': ['c10.png'],
    '單狹縫實驗架設_空間位置示意.svg': ['c16.png'],
    '紙本教材用/單狹縫實驗架設_空間位置示意.svg.png': ['c16.png'],
    '單狹縫繞射_理想圖樣.png': ['c11.png', 'c12.png'],
    '雙狹縫與單狹縫_次波源分布.png': ['c09.png', 'c13.png'],
    '薄膜干涉_實拍與剖面.png': ['photo:肥皂膜薄膜干涉_Yaroslav-Ulyushin_CC-BY-4.0.jpg', 'c14.png'],
    '單狹縫繞射_實拍_文件用.png': ['photo:單狹縫繞射_藍光雷射_Xyqorophibian_CC-BY-SA-4.0.jpg'],
    '生活中的干涉與繞射_實拍.png': ['photo:光碟繞射_Hapecko_CC-BY-SA-4.0.jpg', 'photo:水面油膜_gambier20_CC-BY-2.0.jpg',
                               'photo:肥皂泡薄膜干涉_Pksois23_CC-BY-SA-4.0.jpg', 'photo:孔雀羽毛_Bernard-Spragg_CC0.jpg',
                               'photo:藍閃蝶_Alias0591_CC-BY-2.0.jpg', 'photo:望遠鏡繞射尖峰_ESA-Hubble_CC-BY-4.0.jpg'],
}
PHOTO_CREDIT = {}  # photo file -> 07A licence text (verbatim)


def _collect_credits():
    for b, r0, r1 in ((11, 1, 11), (14, 1, 11), (17, 1, 10)):
        for r in range(r0, r1):
            row = DOC['07A'][b][r]
            fn = os.path.basename('\n'.join(row[1]))
            if fn in PHOTOS:
                PHOTO_CREDIT[fn] = '\n'.join(p for p in row[3] if p != 'Wikimedia來源頁')


_collect_credits()


def img_of(key):
    if key.startswith('photo:'):
        fn = key[6:]
        return {'src': PHOTO_DIR + fn, 'link': PHOTOS[fn], 'credit': PHOTO_CREDIT[fn]}
    c = COMMONS[key]
    return {'src': 'assets/commons/' + key, 'link': c['page'],
            'attrib': f"{c['artist']}｜{c['license']}（Wikimedia Commons：{c['title']}）"}


def media_row(b, r):
    """one 07A row -> media block (07A text verbatim; image = original photo or web replacement)"""
    row = DOC['07A'][b][r]
    kind, path, use, lic = (row[0], row[1], row[2], row[3])
    path = '\n'.join(path)
    fname = os.path.basename(path)
    licence = [p for p in lic if p != 'Wikimedia來源頁']
    blk = {'t': 'media', 'kind': '\n'.join(kind), 'file': path,
           'text': '\n'.join(use), 'credit': '\n'.join(licence)}
    if fname in PHOTOS:
        blk['imgs'] = [{'src': PHOTO_DIR + fname, 'link': PHOTOS[fname]}]
    elif path in WEB:
        blk['imgs'] = [img_of(k) for k in WEB[path]]
        blk['web'] = True
    else:
        blk['missing'] = True
    return blk


SIM_OF = {1: 'superposition', 2: 'ripple', 3: 'doubleslit', 4: 'thinfilm'}


def sim_row(r):
    row = DOC['07A'][4][r]
    return {'t': 'sim', 'sim': SIM_OF[r], 'kind': '\n'.join(row[0]), 'file': '\n'.join(row[1]),
            'text': '\n'.join(row[2])}


RAW = {}
DOCFILE = {}
for f in sorted(glob.glob(os.path.join(SRC_DIR, '[0-9][0-9]*_*.docx'))):
    k = os.path.basename(f).split('_')[0]
    RAW[k] = raw_blocks(f)
    DOCFILE[k] = os.path.basename(f)

DOCIMG = 'assets/docs/'

# ---------------------------------------------------------------- helpers for blocks
def kv(pairs, source):
    """pairs: list of (label, text)"""
    return {'t': 'kv', 'rows': [{'label': l, 'text': x} for l, x in pairs], 'source': source}


def table(head, body, source):
    return {'t': 'table', 'head': head, 'rows': body, 'source': source}


def paras(lst, source=None):
    return {'t': 'paras', 'paras': lst, 'source': source}


def box(kind, title, text, source):
    return {'t': 'box', 'style': kind, 'title': title, 'text': text, 'source': source}


def note(text):
    return {'t': 'note', 'note': text}


def h(title):
    return {'t': 'h', 'title': title}


# ================================================================ TEXTBOOK MODE
NODE_TABLE = {1: 9, 2: 12, 3: 15, 4: 18}
OPENSTAX = {
    1: 'https://openstax.org/books/university-physics-volume-1/pages/16-5-interference-of-waves',
    2: 'https://openstax.org/books/university-physics-volume-3/pages/3-1-youngs-double-slit-interference',
    3: 'https://openstax.org/books/university-physics-volume-3/pages/4-1-single-slit-diffraction',
    4: 'https://openstax.org/books/university-physics-volume-3/pages/3-4-interference-in-thin-films',
}


def node(n):
    b = NODE_TABLE[n]
    t = DOC['01'][b]
    body = [p for p in t[2][1] if p != '（可扣課綱代碼）']
    ref = t[4][1]
    return {
        'name': t[0][1][0],
        'core': T('01', b, 1, 1),
        'body': body,
        'cond': T('01', b, 3, 1),
        'ref': ref,
        'ref_link': OPENSTAX[n],
    }


pages = []

# ---- unit intro
u = DOC['01'][3]
order = DOC['01'][5]
hero = media_row(8, 2)
hero['source'] = '07A'
pages.append({
    'id': 'intro', 'mode': 'book', 'nav': '單元導讀', 'title': '單元導讀　' + T('01', 3, 0, 1),
    'blocks': [
        hero,
        {'t': 'chapters', 'items': [{'target': f'sec{n}', 'label': f'第 {n} 節', 'name': T('01', 5, n, 1).replace('\n', ''),
                                      'text': T('01', 5, n, 2)} for n in (1, 2, 3, 4)], 'source': '01'},
        kv([('適用對象', T('01', 3, 1, 1)), ('核心結論', T('01', 3, 2, 1)),
            ('先備知識', T('01', 3, 3, 1)), ('內容範圍', T('01', 3, 4, 1))], '01'),
        kv([('學習路徑', T('02', 3, 1, 1))], '02'),
        h('知識節點順序'),
        table(['順序', '知識節點名稱', '核心知識', '銜接依據'], rows('01', 5, 1, 5), '01'),
        paras([P('01', 6)], '01'),
    ]})

# ---- sections 1-4 (順序：先實拍／觀察，再模型與互動模擬)
SEC_MEDIA = {
    1: [('sim', 1), ('07A', 8, 5), ('07A', 8, 3), ('sim', 2), ('07A', 8, 6)],
    2: [('07A', 11, 4), ('07A', 11, 10), ('07A', 11, 8), ('07A', 11, 1), ('07A', 11, 5), ('07A', 11, 9),
        ('07A', 11, 6), ('sim', 3), ('07A', 11, 2), ('07A', 11, 3)],
    3: [('07A', 14, 2), ('07A', 14, 3), ('simx', 'singleslit'), ('07A', 14, 1), ('07A', 14, 8), ('07A', 14, 6),
        ('07A', 17, 9)],
    4: [('07A', 17, 8), ('sim', 4)],
}
SEC_LIFE = {
    3: [('07A', 14, 7), ('07A', 17, 1), ('07A', 14, 4)],
    4: [('07A', 17, r) for r in (4, 5, 6)] + [('07A', 14, 5), ('07A', 17, 2),
                                             ('07A', 14, 10), ('07A', 17, 3)],
}
SEC_WS = {1: 'ws1', 2: 'ws2', 3: 'ws3', 4: 'ws3'}


def media_blocks(spec):
    out = []
    for s in spec:
        if s[0] == 'sim':
            blk = sim_row(s[1])
        elif s[0] == 'simx':
            blk = {'t': 'sim', 'sim': s[1], 'text': ''}
        else:
            blk = media_row(s[1], s[2])
        blk['source'] = '07A'
        out.append(blk)
    return out


for n in (1, 2, 3, 4):
    nd = node(n)
    blks = [
        box('core', '學習重點', nd['core'], '01'),
        h('正文'), paras(nd['body'], '01'),
        box('cond', '觀念澄清', nd['cond'], '01'),
        h('圖片與互動模擬'),
    ]
    blks += media_blocks(SEC_MEDIA[n])
    if n in SEC_LIFE:
        blks.append(h('生活中的物理'))
        blks += media_blocks(SEC_LIFE[n])
    blks.append({'t': 'link', 'title': '想想看：前往學習單', 'target': SEC_WS[n]})
    blks.append({'t': 'link', 'title': 'AI 提問守則', 'target': 'ai'})
    if n == 4:
        blks.append({'t': 'link', 'title': '延伸閱讀', 'target': 'ext'})
    blks.append(h('資料來源'))
    blks.append({'t': 'ref', 'paras': nd['ref'], 'link': nd['ref_link'], 'source': '01'})
    name = nd['name']
    pages.append({'id': f'sec{n}', 'mode': 'book', 'nav': f'第 {n} 節　' + name[3:],
                  'title': f'第 {n} 節　' + name[3:], 'blocks': blks})

# ---- worksheets
L02 = DOC['02']


def lesson_rows(b, r0, r1):
    return rows('02', b, r0, r1)


pages.append({
    'id': 'ws1', 'mode': 'book', 'nav': '學習單　第 1 節', 'title': '學習單　' + T('02', 3, 11, 1),
    'blocks': [
        note('第 1 節學習單 Q1–Q8 的題目全文未在原始文件中（待補）。以下為 02 教案中本節的學生活動。'),
        table(['時間', '學生活動與預期表現'], [[r[0], r[2]] for r in lesson_rows(3, 15, 18)], '02'),
        {'t': 'link', 'title': 'AI 提問守則', 'target': 'ai'},
    ]})


def activity(b):
    t = DOC['03'][b]
    title = t[0][1][0]
    return {
        't': 'activity', 'title': title,
        'situation': '\n'.join(t[0][1][1:]),
        'material': T('03', b, 1, 1),
        'questions': C('03', b, 2, 1),
        'answer': T('03', b, 3, 1),
        'guide': T('03', b, 4, 1),
        'source': '03',
    }


ws2 = [
    kv([('對應知識節點', T('03', 3, 1, 1))], '03'),
    table(['順序', '活動名稱', '主要任務與題號', '預計時間'], rows('03', 6, 1, 5), '03'),
    paras([P('03', 7)], '03'),
]
ws2 += [activity(b) for b in (10, 13, 16, 19)]
ws2.append({'t': 'link', 'title': 'AI 提問守則', 'target': 'ai'})
pages.append({'id': 'ws2', 'mode': 'book', 'nav': '學習單　第 2 節',
              'title': '學習單　' + T('02', 4, 1, 1), 'blocks': ws2, 'worksheet': True})

pages.append({
    'id': 'ws3', 'mode': 'book', 'nav': '學習單　第 3 節', 'title': '學習單　' + T('02', 5, 1, 1),
    'blocks': [
        note('第 3 節學習單的題目全文未在原始文件中（待補）。以下為 02 教案中本節的學生活動。'),
        table(['時間', '學生活動與預期表現'], [[r[0], r[2]] for r in lesson_rows(5, 5, 10)], '02'),
        {'t': 'link', 'title': 'AI 提問守則', 'target': 'ai'},
    ]})

# ---- AI rules (verbatim excerpts)
ai = [
    note('以下各條皆直接摘自原始文件，括號內為出處。'),
    h('什麼時候可以問 AI'),
    {'t': 'quote', 'text': T('08', 3, 3, 1), 'source': '08　進入條件'},
    {'t': 'quote', 'text': T('08', 3, 7, 3), 'source': '08　學生操作流程步驟3'},
    {'t': 'quote', 'text': T('08', 5, 4, 1), 'source': '08　啟動條件'},
    {'t': 'quote', 'text': T('08', 3, 8, 2) + '\n' + T('08', 3, 8, 3), 'source': '08　學生操作流程步驟4'},
    h('AI 會怎麼回應'),
    {'t': 'quote', 'text': T('02', 3, 8, 1), 'source': '02　工具與AI'},
    {'t': 'quote', 'text': T('08', 5, 6, 1), 'source': '08　回覆與修訂'},
    h('問完之後'),
    {'t': 'quote', 'text': DOC['06'][31][8][0][0], 'source': '06　後測雙向細目表'},
    {'t': 'quote', 'text': T('02', 5, 9, 3), 'source': '02　第3節45-50分'},
    h('遇到問題時'),
    {'t': 'quote', 'text': T('08', 5, 7, 1), 'source': '08　停止與備援'},
    {'t': 'quote', 'text': T('08', 6, 11, 2), 'source': '08　驗收情境4'},
    {'t': 'quote', 'text': T('02', 3, 9, 1), 'source': '02　替代方案'},
]
pages.append({'id': 'ai', 'mode': 'book', 'nav': 'AI 提問守則', 'title': 'AI 提問守則', 'blocks': ai})

# ---- extension reading (04)
EXT_LINKS = {
    '陽明交大光電系': 'https://dop.nycu.edu.tw/ch/page.html?tID=260',
    '臺灣網路科教館': 'https://www.ntsec.edu.tw/liveSupply/detail.aspx?a=6829&cat=6843&lid=19944&p=1&print=1',
    'OpenStax': 'https://openstax.org/books/university-physics-volume-3/pages/3-introduction',
    '國立自然科學': 'https://web3.nmns.edu.tw/Exhibits/112/the-gravity-realm/unit-4.html',
}


def ext_rows(r0, r1):
    out = []
    for row in rows('04', 3, r0, r1, [0, 1, 2, 3, 4]):
        link = next((v for k, v in EXT_LINKS.items() if row[3].startswith(k)), None)
        out.append({'cells': row, 'link': link})
    return out


ext = [
    paras([P('04', 1)], '04'),
    kv([('核心概念', T('04', 2, 3, 1))], '04'),
    h(T('04', 2, 4, 0)[2:]),
    table(rows('04', 2, 5, 6)[0], rows('04', 2, 6, 12), '04'),
    h(T('04', 3, 0, 0)[2:]),
    paras([T('04', 3, 1, 0)], '04'),
    h(T('04', 3, 2, 0)),
    {'t': 'linktable', 'head': rows('04', 3, 3, 4)[0], 'rows': ext_rows(4, 7), 'source': '04'},
    h(T('04', 3, 7, 0)),
    {'t': 'linktable', 'head': rows('04', 3, 8, 9)[0], 'rows': ext_rows(9, 11), 'source': '04'},
    paras([T('04', 3, 11, 0)], '04'),
]
pages.append({'id': 'ext', 'mode': 'book', 'nav': '延伸閱讀', 'title': '延伸閱讀', 'blocks': ext})

# ---- credits
cred = []
seen = set()
for b, r0, r1 in ((8, 1, 7), (11, 1, 11), (14, 1, 11), (17, 1, 10)):
    for r in range(r0, r1):
        m = media_row(b, r)
        for im in m.get('imgs', []):
            if im['src'] in seen:
                continue
            seen.add(im['src'])
            cred.append({'src': im['src'], 'link': im['link'], 'file': m['file'], 'text': m['text'],
                         'credit': im.get('credit') or (m['credit'] if not m.get('web') else ''),
                         'attrib': im.get('attrib', '')})
def raw_para_links(doc, text_prefix):
    for it in RAW[doc]:
        if isinstance(it, dict) and it.get('text', '').startswith(text_prefix):
            return it['text'], it.get('links', [])
    return '', []


ref_rows = []
for n in (1, 2, 3, 4):
    nd = node(n)
    ref_rows.append({'label': f'第 {n} 節', 'text': '\n'.join(nd['ref']), 'links': [nd['ref_link']]})
f08, l08 = raw_para_links('08', '格式參考')
f10, l10 = raw_para_links('10', '設計參考')
pages.append({'id': 'credits', 'mode': 'book', 'nav': '資料來源與授權', 'title': '資料來源與授權', 'blocks': [
    h('原始文件'),
    note('本網站所有教學文字皆逐字取自以下 10 份原始文件；點選可查看各文件的完整內容。'),
    {'t': 'doclist', 'items': [{'code': k, 'name': DOCNAME[k], 'file': DOCFILE[k], 'target': 'doc_' + k} for k in DOCNAME]},
    h('課文查核依據（依 01）'),
    {'t': 'reflist', 'rows': ref_rows, 'source': '01'},
    h('延伸閱讀資源（依 04）'),
    {'t': 'reflist', 'rows': [{'label': r['cells'][1], 'text': r['cells'][2] + '\n' + r['cells'][3], 'links': ([r['link'], r['link'].replace('3-introduction', '4-introduction')] if 'openstax' in (r['link'] or '') else [r['link']] if r['link'] else [])} for r in ext_rows(4, 7) + ext_rows(9, 11)], 'source': '04'},
    h('設計與格式參考（依 08、10）'),
    {'t': 'reflist', 'rows': [{'label': '08', 'text': f08, 'links': l08}, {'label': '10', 'text': f10, 'links': l10}]},
    h('互動模擬'),
    note('波的疊加、水波干涉、雙狹縫干涉、單狹縫繞射、薄膜干涉等 5 個互動模擬由本網站自行製作（HTML Canvas）。07A 所列原模擬檔未附；「波的疊加」依 07B 模擬需求腳本的參數與操作規格製作。模擬畫面為理想模型，不是實驗實拍。'),
    h('圖片'),
    note('照片與圖片的作者、授權與來源頁如下。標示「網路替代圖」者：原文件列出該圖但未附檔，改用 Wikimedia Commons 上內容相符的開放授權圖片。07B、08 的附圖為原文件內附的示意圖（本教材自製）。'),
    {'t': 'credits', 'items': cred}, paras([P('07A', 1)], '07A')]})

# ================================================================ TEACHER MODE
t_unit = [
    h(T('02', 2, 0, 0)),
    kv([(T('02', 2, 1, 0), T('02', 2, 1, 1)), (T('02', 2, 1, 2), T('02', 2, 1, 3)),
        (T('02', 2, 2, 0), T('02', 2, 2, 1)), (T('02', 2, 2, 2), T('02', 2, 2, 3)),
        (T('02', 2, 3, 0), T('02', 2, 3, 1)), (T('02', 2, 3, 2), T('02', 2, 3, 3)),
        (T('02', 2, 4, 0), T('02', 2, 4, 1)), (T('02', 2, 5, 0), T('02', 2, 5, 1))], '02'),
    h(T('02', 2, 6, 0)),
    kv([(T('02', 2, r, 0), T('02', 2, r, 1)) for r in range(7, 12)] +
       [(T('02', 2, 12, 0), T('02', 2, 12, 1)), (T('02', 2, 12, 2), T('02', 2, 12, 3))], '02'),
    h(T('02', 2, 13, 0)),
    table(rows('02', 2, 14, 15)[0], rows('02', 2, 15, 19), '02'),
    h(T('02', 3, 0, 0)),
    kv([(T('02', 3, 1, 0), T('02', 3, 1, 1))], '02'),
    h(T('02', 3, 2, 0)),
    table(rows('02', 3, 3, 4)[0], rows('02', 3, 4, 7), '02'),
    kv([(T('02', 3, r, 0), T('02', 3, r, 1)) for r in (7, 8, 9)], '02'),
    h('核心教學題目配置'),
    kv([(T('05', 3, r, 0), T('05', 3, r, 1)) for r in range(4)] +
       [(T('05', 5, r, 0), T('05', 5, r, 1)) for r in range(4)], '05'),
    paras([P('05', 6)], '05'),
]
pages.append({'id': 't_unit', 'mode': 'teach', 'nav': '單元教學設計', 'title': '單元教學設計', 'blocks': t_unit})

CARD = {1: [(9, 10), (13, 14)], 2: [(17, 18), (21, 22)], 3: [(26, 27), (31, 32), (36, 37)]}
CARD_REF = {(21, 22): 23, (26, 27): 28, (31, 32): 33}


def card(i, hb, bb):
    t = DOC['05'][bb]
    blk = {'t': 'card', 'title': f'核心教學題目卡 {i}',
           'meta': [T('05', hb, 1, 0), T('05', hb, 1, 1), T('05', hb, 1, 2)],
           'rows': [{'label': T('05', bb, r, 0).replace('\n', ''), 'text': T('05', bb, r, 1)}
                    for r in range(len(t))], 'source': '05'}
    if (hb, bb) in CARD_REF:
        blk['foot'] = P('05', CARD_REF[(hb, bb)])
    return blk


DIFF_ROWS = {1: (5, 7), 2: (7, 9), 3: (9, 10)}
GUIDE = {1: [6], 2: [4], 3: [8]}


def guide_table(b):
    t = DOC['10'][b]
    return {'t': 'guide', 'title': T('10', b, 0, 0),
            'kv': [(T('10', b, 1, 0), T('10', b, 1, 1)), (T('10', b, 1, 2), T('10', b, 1, 3)),
                   (T('10', b, 2, 0), T('10', b, 2, 1)), (T('10', b, 3, 0), T('10', b, 3, 1))],
            'head': rows('10', b, 4, 5)[0], 'rows': rows('10', b, 5, 8), 'source': '10'}


LESSON = {1: (3, 11), 2: (4, 1), 3: (5, 1)}
NODES_OF = {1: [1], 2: [2], 3: [3, 4]}
ci = 0
for n in (1, 2, 3):
    b, r = LESSON[n]
    blks = [
        kv([(T('02', b, r, 2), T('02', b, r, 3)), (T('02', b, r + 1, 0), T('02', b, r + 1, 1)),
            (T('02', b, r + 2, 0), T('02', b, r + 2, 1))], '02'),
        table(rows('02', b, r + 3, r + 4)[0], rows('02', b, r + 4, r + 4 + (3 if n == 1 else 5)), '02'),
    ]
    gi = r + 4 + (3 if n == 1 else 5)
    blks += [h(T('02', b, gi, 0)),
             kv([(T('02', b, gi + 1, 0), T('02', b, gi + 1, 1)),
                 (T('02', b, gi + 2, 0), T('02', b, gi + 2, 1))], '02')]
    for nn in NODES_OF[n]:
        nd = node(nn)
        blks.append(box('cond', '成立條件與易混淆處　' + nd['name'], nd['cond'], '01'))
    if n == 2:
        blks.append(h('學習單教師版'))
        blks.append(kv([('學習目標與產出', T('03', 3, 2, 1))], '03'))
        for ab in (10, 13, 16, 19):
            blks.append({'t': 'tans', 'title': DOC['03'][ab][0][1][0],
                         'answer': T('03', ab, 3, 1), 'guide': T('03', ab, 4, 1),
                         'material': T('03', ab, 1, 1), 'source': '03'})
    blks.append(h('核心教學題目卡'))
    for hb, bb in CARD[n]:
        ci += 1
        blks.append(card(ci, hb, bb))
    blks.append(h('常見學習困難與引導'))
    d0, d1 = DIFF_ROWS[n]
    blks.append(table(rows('10', 2, 4, 5)[0], rows('10', 2, d0, d1), '10'))
    blks.append(paras([P('10', 3)], '10'))
    for gb in GUIDE[n]:
        blks.append(guide_table(gb))
    if n == 2:
        blks.append(h(T('08', 5, 0, 0)[2:]))
        blks.append(paras([T('08', 5, 1, 0)], '08'))
        blks.append(kv([(T('08', 5, 2, 0), T('08', 5, 2, 1)), (T('08', 5, 2, 2), T('08', 5, 2, 3))] +
                       [(T('08', 5, k, 0), T('08', 5, k, 1)) for k in range(3, 8)], '08'))
        blks.append(h(T('08', 5, 8, 0)))
        blks.append(table(rows('08', 5, 9, 10)[0], rows('08', 5, 10, 12), '08'))
    blks.append({'t': 'link', 'title': '對應教科書內容', 'target': 'sec%d' % NODES_OF[n][0]})
    pages.append({'id': f't{n}', 'mode': 'teach', 'nav': f'第 {n} 節授課',
                  'title': T('02', b, r, 1), 'blocks': blks})

# ---- assessment & records
pages.append({'id': 't_assess', 'mode': 'teach', 'nav': '評量與學習記錄', 'title': T('02', 6, 0, 0)[2:], 'blocks': [
    table(rows('02', 6, 1, 2)[0], rows('02', 6, 2, 6), '02'),
    kv([(T('02', 6, 6, 0), T('02', 6, 6, 1))], '02'),
    {'t': 'link', 'title': '試題評量（雙向細目表）', 'target': 't_exam'},
    h(T('02', 6, 7, 0)[2:]),
    table(rows('02', 6, 8, 9)[0], rows('02', 6, 9, 13), '02'),
    kv([(T('02', 6, 13, 0), T('02', 6, 13, 1))], '02'),
]})

# ---- difficulties overview
pages.append({'id': 't_diff', 'mode': 'teach', 'nav': '學習困難總覽', 'title': '常見學習困難與引導策略', 'blocks': [
    paras([P('10', 1)], '10'),
    kv([(T('10', 2, 0, 0), T('10', 2, 0, 1)), (T('10', 2, 0, 2), T('10', 2, 0, 3)),
        (T('10', 2, 1, 0), T('10', 2, 1, 1)), (T('10', 2, 1, 2), T('10', 2, 1, 3)),
        (T('10', 2, 2, 0), T('10', 2, 2, 1))], '10'),
    h(T('10', 2, 3, 0)[2:]),
    table(rows('10', 2, 4, 5)[0], rows('10', 2, 5, 10), '10'),
    paras([P('10', 3)], '10'),
    guide_table(4), guide_table(6), guide_table(8),
    paras([P('10', 9), P('10', 10)], '10'),
]})

# ---- media & digital planning (07A sims, 07B, 08)
m07 = [
    paras([P('07A', 1), T('07A', 2, 0, 1)], '07A'),
    h(P('07A', 3)),
    table(['編號與類型', '素材與檔案位置', '知識節點與用途', '使用需求與來源'], rows('07A', 4, 1, 5), '07A'),
    paras([P('07A', 5)], '07A'),
    h(P('07A', 6)), paras([P('07A', 7)], '07A'),
    table(['編號與類型', '素材與檔案位置', '知識節點與用途', '使用需求與來源'], rows('07A', 8, 1, 7), '07A'),
    h(P('07A', 9)), paras([P('07A', 10)], '07A'),
    table(['編號與類型', '素材與檔案位置', '知識節點與用途', '使用需求與來源'], rows('07A', 11, 1, 11), '07A'),
    h(P('07A', 12)), paras([P('07A', 13)], '07A'),
    table(['編號與類型', '素材與檔案位置', '知識節點與用途', '使用需求與來源'], rows('07A', 14, 1, 11), '07A'),
    h(P('07A', 15)), paras([P('07A', 16)], '07A'),
    table(['編號與類型', '素材與檔案位置', '知識節點與用途', '使用需求與來源'], rows('07A', 17, 1, 10), '07A'),
]
pages.append({'id': 't_media', 'mode': 'teach', 'nav': '多模態素材清單', 'title': T('07A', 2, 0, 1).split('／')[1] + '　' + P('07A', 0)[5:], 'blocks': m07})

b07 = [
    h(P('07B', 0)), paras([P('07B', 1)], '07B'),
    kv([(T('07B', 2, r, 0).replace('\n', ''), T('07B', 2, r, 1)) for r in range(6)], '07B'),
    paras([P('07B', 3)], '07B'),
    h(P('07B', 4)), paras([P('07B', 6)], '07B'),
    {'t': 'media', 'kind': '07B', 'file': '', 'text': P('07B', 8), 'credit': '',
     'src': DOCIMG + '07B_同向反向完全重疊比較圖.png', 'source': '07B'},
    h(P('07B', 9)), paras([P('07B', 10)], '07B'),
    kv([(T('07B', 11, r, 0).replace('\n', ''), T('07B', 11, r, 1)) for r in range(2)], '07B'),
    paras([P('07B', 12)], '07B'),
]
shots = [rows('07B', 13, 1, 3), rows('07B', 16, 1, 4)]
k = 0
for grp in shots:
    for row in grp:
        k += 1
        b07.append({'t': 'shot', 'cells': row, 'head': ['編號／時間', '畫面內容或草圖', '旁白與字幕', '動作與轉場', '備註與素材'],
                    'src': DOCIMG + f'07B_動畫分鏡0{k}.png', 'source': '07B'})
b07 += [
    kv([(T('07B', 17, 0, 0).replace('\n', ''), T('07B', 17, 0, 1))], '07B'),
    paras([P('07B', 18)], '07B'),
    h(P('07B', 19)), paras([P('07B', 20)], '07B'),
    kv([(T('07B', 21, r, 0).replace('\n', ''), T('07B', 21, r, 1)) for r in range(4)], '07B'),
    h(P('07B', 22)), paras([P('07B', 23)], '07B'),
    table(rows('07B', 24, 0, 1)[0], rows('07B', 24, 1, 7), '07B'),
    paras([P('07B', 25)], '07B'),
    h(P('07B', 28)),
    table(['操作項目', '操作與條件', '畫面結果與回饋'], rows('07B', 29, 1, 5), '07B'),
    kv([(T('07B', 30, r, 0).replace('\n', ''), T('07B', 30, r, 1)) for r in range(2)], '07B'),
    h(P('07B', 31)), paras([P('07B', 32)], '07B'),
    {'t': 'media', 'kind': '07B', 'file': '', 'text': P('07B', 34), 'credit': '',
     'src': DOCIMG + '07B_模擬介面示意圖.png', 'source': '07B'},
]
pages.append({'id': 't_07b', 'mode': 'teach', 'nav': '波的疊加需求腳本', 'title': '多模態輔助教材需求腳本', 'blocks': b07})

d08 = DOC['08']
p08 = [
    paras([P('08', 1)], '08'),
    h(T('08', 2, 0, 0)[2:]),
    kv([(T('08', 2, 1, 0), T('08', 2, 1, 1)), (T('08', 2, 1, 2), T('08', 2, 1, 3)),
        (T('08', 2, 2, 0), T('08', 2, 2, 1)), (T('08', 2, 2, 2), T('08', 2, 2, 3))] +
       [(T('08', 2, k, 0), T('08', 2, k, 1)) for k in (3, 4, 5)], '08'),
    h(T('08', 2, 6, 0)[2:]), paras([T('08', 2, 7, 0)], '08'),
    table(rows('08', 2, 8, 9, [0, 1, 2, 3])[0], rows('08', 2, 9, 13, [0, 1, 2, 3]), '08'),
    h(T('08', 3, 0, 0)[2:]), paras([T('08', 3, 1, 0)], '08'),
    kv([(T('08', 3, 2, 0), T('08', 3, 2, 1)), (T('08', 3, 2, 2), T('08', 3, 2, 3)),
        (T('08', 3, 3, 0), T('08', 3, 3, 1))], '08'),
    table(rows('08', 3, 4, 5)[0], rows('08', 3, 5, 10), '08'),
    h(T('08', 4, 0, 0)), paras([T('08', 4, 1, 0)], '08'),
    kv([(T('08', 4, 2, 0), T('08', 4, 2, 1)), (T('08', 4, 2, 2), T('08', 4, 2, 3))], '08'),
    {'t': 'media', 'kind': '08', 'file': '', 'text': '', 'credit': '',
     'src': DOCIMG + '08_Q4畫面草圖.png', 'source': '08'},
    kv([(T('08', 4, 4, 0), T('08', 4, 4, 1)), (T('08', 4, 5, 0), T('08', 4, 5, 1))], '08'),
    h(T('08', 6, 0, 0)[2:]), paras([T('08', 6, 1, 0)], '08'),
    kv([(T('08', 6, k, 0), T('08', 6, k, 1)) for k in (2, 3, 4, 5)], '08'),
    h(T('08', 6, 6, 0)),
    table(rows('08', 6, 7, 8, [0, 1, 2])[0], rows('08', 6, 8, 13, [0, 1, 2]), '08'),
    h(T('08', 6, 13, 0)),
    kv([(T('08', 6, k, 0), T('08', 6, k, 1)) for k in (14, 15)], '08'),
    paras([P('08', 7)], '08'),
]
pages.append({'id': 't_08', 'mode': 'teach', 'nav': '數位教材整合規劃', 'title': P('08', 0), 'blocks': p08})

EXAM_RAW = []
pages.append({'id': 't_exam', 'mode': 'teach', 'nav': '試題評量', 'title': '試題評量　雙向細目表', 'blocks': [
    note('以下為 06 評量雙向細目表的完整內容（前測、隨堂測驗第3節、後測）。各測驗的題目本身不在 10 份原始文件中，將另行提供。'),
    {'t': 'docraw', 'items': RAW['06'], 'source': '06'}]})


# ================================================================ TEACHER SLIDE DECKS
N = {n: node(n) for n in (1, 2, 3, 4)}


def tx(n, *idx):
    """textbook paragraphs of section n (verbatim) with their position label"""
    return {'ref': f'課本第 {n} 節　正文第 ' + '、'.join(str(i + 1) for i in idx) + ' 段',
            'paras': [N[n]['body'][i] for i in idx], 'target': f'sec{n}'}


def cpt(label, text, source):
    return {'label': label, 'text': text, 'source': source}


def card_field(bb, r, label=None):
    return cpt(label or T('05', bb, r, 0).replace('\n', ''), T('05', bb, r, 1), '05')


def img(key, cap=''):
    if key.startswith('photo:') or key in COMMONS:
        d = img_of(key)
    else:
        d = {'src': key}
    d['cap'] = cap
    return d


def seg(b, r):
    row = rows('02', b, r, r + 1)[0]
    act = row[1].split('\n')
    ask = [x for x in act if x.startswith('問：')]
    do = [x for x in act if not x.startswith('問：')]
    return {'time': row[0].replace('\n', ''), 'do': '\n'.join(do), 'ask': '\n'.join(ask),
            'student': row[2], 'evidence': row[3], 'material': row[4]}


def diff(r):
    row = rows('10', 2, r, r + 1)[0]
    return {'label': '常見學習困難：' + row[0].replace('\n', ' '), 'rows': [
        ('學生表現', row[1]), ('引導方式', row[2]), ('改善判準', row[3])], 'source': '10'}


def guide_notes(b):
    t = rows('10', b, 5, 8)
    return {'label': T('10', b, 0, 0) + '：' + T('10', b, 1, 1), 'rows': [(x[0].replace('\n', ' '), x[1]) for x in t],
            'source': '10'}


def ws_note(ab):
    return {'label': '學習單 ' + DOC['03'][ab][0][1][0], 'rows': [('參考答案與判讀', T('03', ab, 3, 1)),
                                                              ('常見錯誤與引導', T('03', ab, 4, 1))], 'source': '03'}


def title_slide(b, r, ov_row, goals):
    return {'kind': 'title', 'title': T('02', b, r, 1), 'time': T('02', b, r, 3),
            'kv': [cpt('核心問題', T('02', 3, ov_row, 2), '02'), cpt('本節功能', T('02', 3, ov_row, 1), '02'),
                   cpt(T('02', b, r + 1, 0), T('02', b, r + 1, 1), '02'),
                   cpt(T('02', b, r + 2, 0), T('02', b, r + 2, 1), '02')] +
                  [cpt('學習目標 ' + T('02', 2, g, 0), T('02', 2, g, 1), '02') for g in goals]}


decks = {
 1: [
  title_slide(3, 11, 4, [15, 18]),
  dict(seg(3, 15), heading='兩個脈衝相遇', text=tx(1, 0), sim='superposition',
       images=[img('c03.png', '網路替代圖：繩波相遇前')],
       concept=[cpt('專業說明', T('02', 3, 19, 1), '02'), card_field(10, 4, '答案要素（題目卡1）')],
       notes=[diff(5), guide_notes(6), {'label': '題目卡1　常見迷思與錯誤', 'rows': [('', T('05', 10, 5, 1))], 'source': '05'}]),
  dict(seg(3, 15), heading='完全建設性干涉與完全破壞性干涉', text=tx(1, 1), sim='superposition',
       concept=[cpt('核心理解', N[1]['core'], '01'), card_field(10, 2, '核心問題（題目卡1）')],
       notes=[{'label': '條件與誤解', 'rows': [('', T('02', 3, 20, 1))], 'source': '02'},
              {'label': '題目卡1　成功規準', 'rows': [('', T('05', 10, 6, 1))], 'source': '05'}]),
  dict(seg(3, 16), heading='水波干涉：位移與振幅', text=tx(1, 2, 3), sim='ripple',
       images=[img('c02.jpg', '網路替代圖：水波槽中的兩點波源干涉'), img('c04.png', '網路替代圖：雙點波源干涉')],
       concept=[card_field(14, 2, '核心問題（題目卡2）'), card_field(14, 4, '答案要素（題目卡2）')],
       notes=[diff(6), {'label': '題目卡2　常見迷思與錯誤', 'rows': [('', T('05', 14, 5, 1))], 'source': '05'},
              {'label': '題目卡2　預期證據', 'rows': [('', T('05', 14, 3, 1))], 'source': '05'}]),
  dict(seg(3, 17), heading='命名腹線、節線，再反思', text=tx(1, 3), sim='ripple',
       concept=[cpt('成立條件與易混淆處', N[1]['cond'], '01'), card_field(14, 4, '答案要素（題目卡2）')],
       notes=[{'label': '題目卡2　成功規準', 'rows': [('', T('05', 14, 6, 1))], 'source': '05'},
              {'label': '條件與誤解', 'rows': [('', T('02', 3, 20, 1))], 'source': '02'}]),
 ],
 2: [
  title_slide(4, 1, 5, [16, 18]),
  dict(seg(4, 5), heading='修訂水波 CER',
       concept=[card_field(14, 4, '答案要素（題目卡2）')],
       notes=[{'label': '題目卡2　成功規準', 'rows': [('', T('05', 14, 6, 1))], 'source': '05'}]),
  dict(seg(4, 6), heading='先預測：屏幕上會看到什麼？',
       images=[img('c08.jpg', '網路替代圖：雙狹縫實驗架設'), img('c10.png', '網路替代圖：直進模型的預測')],
       reveal=img('photo:雙狹縫干涉_紅光實拍_Bryan-Tong-Minh_PD.jpg', '632.8 nm紅光雙狹縫實拍'),
       worksheet=C('03', 10, 2, 1),
       concept=[card_field(18, 2, '核心問題（題目卡3）')],
       notes=[ws_note(10)]),
  dict(seg(4, 7), heading='觀察實拍，再用模擬比較', text=tx(2, 0), sim='doubleslit',
       images=[img('photo:雙狹縫干涉_紅光實拍_Bryan-Tong-Minh_PD.jpg', '632.8 nm紅光雙狹縫實拍')],
       concept=[card_field(18, 4, '答案要素（題目卡3）'), card_field(18, 3, '預期證據（題目卡3）')],
       notes=[ws_note(13), diff(8), {'label': '題目卡3　常見迷思與錯誤', 'rows': [('', T('05', 18, 5, 1))], 'source': '05'}]),
  dict(seg(4, 8), heading='用惠更斯原理解釋 B 亮、D 暗', text=tx(2, 1, 2), sim='doubleslit',
       images=[img('c13.png', '網路替代圖：惠更斯原理'), img('c09.png', '網路替代圖：兩個相干點波源的波前')],
       concept=[cpt('專業說明', T('02', 4, 11, 1), '02'), card_field(22, 4, '答案要素（題目卡4）')],
       notes=[ws_note(16), diff(7), guide_notes(4),
              {'label': 'AI回應檢查例', 'rows': [r for x in rows('08', 5, 10, 12) for r in (('學生輸入', x[0]), ('可接受的引導', x[1]), ('不應出現的回覆', x[2]))], 'source': '08'}]),
  dict(seg(4, 9), heading='比較水波與光，寫出完整解釋', text=tx(2, 3),
       images=[img('c07.png', '網路替代圖：雙狹縫亮暗條紋')],
       concept=[cpt('成立條件與易混淆處', N[2]['cond'], '01'), card_field(22, 6, '成功規準（題目卡4）')],
       notes=[ws_note(19), {'label': '條件與誤解', 'rows': [('', T('02', 4, 12, 1))], 'source': '02'}]),
 ],
 3: [
  title_slide(5, 1, 6, [17, 18]),
  dict(seg(5, 5), heading='哪句把模型當成實驗證據？',
       images=[img('photo:雙狹縫干涉_紅光實拍_Bryan-Tong-Minh_PD.jpg', '實拍'), img('c09.png', '網路替代圖：模型')],
       concept=[card_field(18, 3, '預期證據（題目卡3）')],
       notes=[diff(8)]),
  dict(seg(5, 6), heading='單狹縫繞射：中央與兩側亮紋', text=tx(3, 0, 1, 2), sim='singleslit',
       images=[img('photo:單狹縫繞射_藍光雷射_Xyqorophibian_CC-BY-SA-4.0.jpg', '單狹縫繞射實拍'), img('c16.png', '網路替代圖：單狹縫繞射')],
       concept=[cpt('專業說明', T('02', 5, 11, 1), '02'), card_field(27, 4, '答案要素（題目卡5）')],
       notes=[{'label': '成立條件與易混淆處', 'rows': [('', N[3]['cond'])], 'source': '01'},
              {'label': '題目卡5　常見迷思與錯誤', 'rows': [('', T('05', 27, 5, 1))], 'source': '05'}]),
  dict(seg(5, 6), heading='比較雙狹縫與單狹縫的次波源分布', text=tx(3, 3), sim='singleslit',
       images=[img('c09.png', '網路替代圖：兩個點波源'), img('c13.png', '網路替代圖：縫內許多次波源')],
       concept=[card_field(27, 2, '核心問題（題目卡5）'), card_field(27, 6, '成功規準（題目卡5）')],
       notes=[diff(9), guide_notes(8)]),
  dict(seg(5, 7), heading='薄膜：哪兩束反射光會重疊？', text=tx(4, 0, 1, 2), sim='thinfilm',
       images=[img('photo:肥皂膜薄膜干涉_Yaroslav-Ulyushin_CC-BY-4.0.jpg', '肥皂膜'), img('c14.png', '網路替代圖：薄膜剖面'),
               img('photo:水面油膜_gambier20_CC-BY-2.0.jpg', '水面油膜')],
       concept=[card_field(32, 4, '答案要素（題目卡6）')],
       notes=[{'label': '題目卡6　常見迷思與錯誤', 'rows': [('', T('05', 32, 5, 1))], 'source': '05'},
              {'label': '題目卡6　成功規準', 'rows': [('', T('05', 32, 6, 1))], 'source': '05'},
              {'label': '條件與誤解', 'rows': [('', T('02', 5, 12, 1))], 'source': '02'},
              {'label': '成立條件與易混淆處', 'rows': [('', N[4]['cond'])], 'source': '01'}]),
  dict(seg(5, 8), heading='直進模型漏掉了什麼？', text=tx(4, 3),
       images=[img('photo:雙狹縫干涉_紅光實拍_Bryan-Tong-Minh_PD.jpg', '雙狹縫實拍'),
               img('photo:單狹縫繞射_藍光雷射_Xyqorophibian_CC-BY-SA-4.0.jpg', '單狹縫實拍')],
       concept=[card_field(37, 2, '核心問題（題目卡7）'), card_field(37, 4, '答案要素（題目卡7）')],
       notes=[{'label': '題目卡7　常見迷思與錯誤', 'rows': [('', T('05', 37, 5, 1))], 'source': '05'},
              {'label': '題目卡7　成功規準', 'rows': [('', T('05', 37, 6, 1))], 'source': '05'}]),
  dict(seg(5, 9), heading='反思：哪項證據改變你的想法？',
       concept=[cpt('達成規準（學習目標 4）', T('02', 2, 18, 3), '02'), cpt('單元結束', T('02', 6, 5, 1) + '\n' + T('02', 6, 5, 2), '02')],
       notes=[{'label': '數位記錄', 'rows': [('', T('02', 6, 6, 1))], 'source': '02'}]),
 ],
}
for n in (1, 2, 3):
    pages.append({'id': f'd{n}', 'mode': 'teach', 'nav': f'第 {n} 節上課簡報', 'title': T('02', LESSON[n][0], LESSON[n][1], 1),
                  'deck': decks[n], 'blocks': [], 'lesson': f't{n}'})
for pg in pages:
    if pg['id'] in ('t1', 't2', 't3'):
        pg['nav'] = pg['nav'].replace('授課', '教案全文')


# ================================================================ 原始文件全文（10 份文件完整呈現）
for k in ['01', '02', '03', '04', '05', '06', '07A', '07B', '08', '10']:
    pages.append({'id': 'doc_' + k, 'mode': 'teach', 'nav': k + '　' + DOCNAME[k], 'title': k + '　' + DOCNAME[k],
                  'blocks': [note('本頁完整呈現原始文件「' + DOCFILE[k] + '」的全部內容（含表格與附圖）；灰色斜體為原文件中的填寫提示。'),
                             {'t': 'docraw', 'items': RAW[k], 'source': k}]})

out = {
    'title': '干涉與繞射',
    'docfiles': DOCFILE,
    'subtitle': T('01', 3, 1, 1).split('；')[0],
    'sources': DOCNAME,
    'pages': pages,
}
json.dump(out, open(os.path.join(SITE, 'content.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(DOC, open(os.path.join(SITE, 'tools', 'source_text.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('pages', len(pages))
