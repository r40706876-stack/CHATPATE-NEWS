"""News-first editorial path, authorized 2 November 2026.
No comedy quota, viral-score gate, script length, word count or cast quota.
"""
import datetime as dt
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import gemini

QUERIES = {
    'जेब/महंगाई': 'भारत राष्ट्रीय LPG पेट्रोल महंगाई उपभोक्ता नया बदलाव',
    'बैंकिंग/भुगतान': 'RBI NPCI UPI बैंक ग्राहक देशभर नया नियम',
    'नौकरी/पढ़ाई': 'भारत राष्ट्रीय रोजगार भर्ती परीक्षा शिक्षा महत्वपूर्ण बदलाव',
    'रेलवे/यात्रा नियम': 'भारतीय रेलवे देशभर यात्री टिकट रिफंड आरक्षण नियम बदलाव',
    'मोबाइल/डिजिटल सुरक्षा': 'TRAI भारत मोबाइल रिचार्ज स्पैम साइबर ठगी राष्ट्रीय चेतावनी',
    'जनहित/अधिकार': 'भारत राष्ट्रीय जनहित पेंशन उपभोक्ता अधिकार आधिकारिक सूचना',
}
BRIEF = '''दर्शक पूरे भारत में हैं। केवल NATIONAL-RELEVANCE खबर चुनो: अलग-अलग राज्यों के आम लोगों
की जेब, नौकरी, पढ़ाई, बैंकिंग, मोबाइल, अधिकार या रोजमर्रा पर सीधा और व्यापक असर।
एक शहर/जिले की घटना, किसी एक रूट पर नई ट्रेन, उद्घाटन, स्थानीय मौसम/अपराध या केवल एक क्षेत्र
के लोगों के काम की खबर मुख्य विषय नहीं। राष्ट्रीय अखबार में छपना राष्ट्रीय असर का प्रमाण नहीं।
रेलवे का देशभर में लागू टिकट/रिफंड/आरक्षण नियम लिया जा सकता है; बेंगलुरु-मुंबई जैसी एक ट्रेन नहीं।
'सब इससे relate करेंगे' कहने भर से local खबर को national मत बनाओ; स्रोतों से व्यापक असर साबित हो।
देशभर की महत्वपूर्ण खबर न मिले तो साफ रुक जाओ; local/comedy fallback नहीं।
बकरा न्यूज़ अब NEWS-FIRST है: जरूरी, ताजा, विश्वसनीय खबर और उसका लोगों पर असर मुख्य है।
खबर को मजाकिया/वायरल/अजीब होने की जरूरत नहीं। महत्व = असर, तात्कालिकता, उपयोगिता और प्रमाण।
मजाक या हल्का पंच तभी जब स्वाभाविक हो; जरूरत न हो तो बिल्कुल नहीं। पीड़ितों पर मजाक नहीं।
समय, शब्द, पहली line, lines, किरदारों की संख्या, punch की संख्या का कोई तय कोटा नहीं।
खबर पूरी और साफ समझ आए जितनी लंबाई चाहिए उतनी रखो; अनावश्यक दोहराव हटाओ।
सवाल, सीधी headline, explanation, संवाद सभी स्वीकार्य। loop, tag/share/follow मांगना, suspense,
पहले तीन सेकंड में हंसी, हर line में joke या कई किरदार अनिवार्य नहीं। जरूरी बात आखिर तक छिपाओ मत।
नीति/आदेश की तटस्थ जानकारी स्वीकार्य; पार्टी प्रचार और बेवजह राजनीतिक तंज नहीं।
तथ्य, तारीख, राशि, लागू क्षेत्र, प्रस्ताव बनाम लागू नियम और अपवाद सही हों। अज्ञात बात साफ बताओ।
मनगढ़ंत उद्धरण, फीस, आंकड़ा, 'विशेषज्ञों का कहना है' या मजाक को असली खबर की तरह नहीं लिखना।
'''


def require_national(item):
    """Editorial audience scope, separate from entertainment/length preferences."""
    if item.get('scope_class') != 'national' or not str(item.get('national_relevance', '')).strip():
        raise ValueError('Only nationally relevant news is allowed; local/route-only news is excluded')


def collect(feed_file=None):
    import topics
    rows, seen = [], set()
    for cat, query in QUERIES.items():
        url = 'https://news.google.com/rss/search?q=' + urllib.parse.quote(query + ' when:3d') + '&hl=hi&gl=IN&ceid=IN:hi'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                root = ET.fromstring(response.read())
            for item in list(root.iter('item'))[:6]:
                title = (item.findtext('title') or '').strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                rows.append({'title': title, 'category': cat, 'url': item.findtext('link') or '',
                             'published': item.findtext('pubDate') or ''})
        except Exception as exc:
            print('News feed unavailable:', cat, type(exc).__name__)
    if not rows:
        raise RuntimeError('Important-news sources unavailable; refusing comedy/demo fallback')
    return {'important_news': rows, 'recent': [t for _, _, t in topics.history(7)]}


def normalize(ep):
    """Validate renderable structure without shortening or rewriting editorial content."""
    from news_writer import EXPRS, SETS_OK, pick_set
    if not isinstance(ep, dict) or not isinstance(ep.get('lines'), list) or not ep['lines']:
        raise ValueError('News script has no lines')
    for line in ep['lines']:
        if line.get('who') not in {'bablu', 'ramesh', 'chacha', 'pinky', 'dadi'} or not str(line.get('say', '')).strip():
            raise ValueError('Invalid speaker or empty news line')
        line.setdefault('caption', line['say'])
        if line.get('expr') not in EXPRS:
            line['expr'] = 'gambhir'
        if line.get('set') not in SETS_OK:
            line['set'] = pick_set(line['who'], line['say'], ep.get('topic', ''))
        line.setdefault('visuals', [])
        line.setdefault('photo_hi', [])
    ep.update(editorial_mode='news_first', writer='news_first', format='news', label='जरूरी खबर')
    ep.setdefault('hook', ep['lines'][0]['say'])
    ep.setdefault('hook_text', ep['lines'][0]['say'])
    ep.setdefault('ticker', [])
    ep['no_clips'] = True  # Search clips are disabled until event provenance is available.
    for line in ep['lines']:
        line['_news_first'] = True
        line['_news_sources'] = ep.get('sources', [])
    return ep


def write(c, n=1):
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).isoformat()
    picks = gemini.ask_json(BRIEF + '\nआज IST: ' + today + '\nखबरों की सूची:\n' + json.dumps(c, ensure_ascii=False) +
        f'\nसिर्फ {n} सबसे महत्वपूर्ण विषय चुनो। हाल की खबर में जरूरी नई जानकारी हो तो फिर ले सकते हो। '
        'सिर्फ JSON list: [{"topic":"...", "importance_reason":"किस पर क्या असर", "query":"...", "scope_class":"national", "national_relevance":"अलग राज्यों के किन लोगों पर क्या सीधा असर"}]',
        json_mode=True, temperature=0.2)
    if not isinstance(picks, list) or not picks:
        raise ValueError('No important news selected')
    episodes = []
    for pick in picks[:n]:
        require_national(pick)
        facts = gemini.ask_json(BRIEF + '\nआज IST: ' + today + '\nGoogle Search से इस विषय की वर्तमान जानकारी जाँचो: ' +
            json.dumps(pick, ensure_ascii=False) + '\nशीर्षक से निष्कर्ष मत निकालो। मूल आधिकारिक नोटिस/दस्तावेज '
            'प्राथमिकता है; उपलब्ध न हो तो विश्वसनीय रिपोर्ट का सही श्रेय और सीमा बताओ। '
            'स्रोत में न मिले अंक/तारीख मत जोड़ो। पुष्टि न हो तो publishable=false। '
            'सिर्फ JSON: {"publishable":true,"topic":"...","importance_reason":"...","scope_class":"national","national_relevance":"स्रोतों से व्यापक असर का प्रमाण",'
            '"facts":[{"id":"f1","text":"...","source_ids":["s1"]}],'
            '"sources":[{"id":"s1","name":"...","url":"https://...","date":"..."}],'
            '"unknowns":[],"scope":"कहां/किस पर लागू","action":"दर्शक को क्या करना है"}',
            search=True, temperature=0.1)
        if not isinstance(facts, dict) or facts.get('publishable') is not True:
            raise ValueError('News facts could not be confirmed')
        require_national(facts)
        sources = facts.get('sources') or []
        if not sources or any(not isinstance(s, dict) or urllib.parse.urlparse(str(s.get('url', ''))).scheme not in ('https', 'http')
                              or not s.get('name') or not s.get('id') for s in sources):
            raise ValueError('Missing news source references')
        source_ids = {s['id'] for s in sources}
        rows = facts.get('facts') or []
        if not rows or any(not f.get('id') or not f.get('text') or not f.get('source_ids') or
                           not set(f['source_ids']) <= source_ids for f in rows):
            raise ValueError('Facts missing source mapping')
        ep = gemini.ask_json(BRIEF + '\nसिर्फ नीचे के source-backed तथ्य इस्तेमाल करो:\n' + json.dumps(facts, ensure_ascii=False) +
            '\nएक पूरी Hindi news script लिखो। बबलू मुख्य reporter है, बाकी किरदार जरूरत पर। '
            'स्पष्ट करो: क्या हुआ, किस पर असर, कब/कहाँ लागू, जरूरी अपवाद, अब क्या करें। '
            'प्रत्येक factual line के fact_ids दो; satire line को satire=true और तथ्य से अलग साफ रखो। '
            'visuals उसी बात को दिखाएं; काल्पनिक घटना को असली footage मत बताओ। '
            'सिर्फ एक JSON object: {"topic":"...","breaking":"...","hook_short":"...",'
            '"lines":[{"who":"bablu","say":"...","caption":"...","fact_ids":["f1"],'
            '"satire":false,"expr":"gambhir","set":"studio","visuals":["specific English search"],'
            '"photo_hi":["सटीक हिंदी खोज"]}],"caption_post":"सार और स्रोत"}', json_mode=True, temperature=0.6)
        ep = normalize(ep)
        fact_ids = {f['id'] for f in rows}
        for line in ep['lines']:
            if line.get('satire') is not True and (not line.get('fact_ids') or not set(line['fact_ids']) <= fact_ids):
                raise ValueError('News line has no valid fact reference')
        review = gemini.ask_json(BRIEF + '\nतथ्य और script की संपादकीय जाँच करो। अवधि/comedy/tag पर अंक नहीं। '
            'क्या राष्ट्रीय असर स्रोत में साबित है, या यह केवल स्थानीय/एक रूट की खबर है? national_scope_ok उसी आधार पर दो। हर line का दावा प्रमाण से मिलता है? scope/date/exception सही? कोई जरूरी बात छूटी या satire तथ्य जैसा है? '
            + json.dumps({'facts': facts, 'script': ep}, ensure_ascii=False) +
            '\nJSON: {"ok":true,"national_scope_ok":true,"issues":[]}', json_mode=True, temperature=0.1)
        if not isinstance(review, dict) or review.get('ok') is not True or review.get('national_scope_ok') is not True or review.get('issues'):
            raise ValueError('News editorial review failed: ' + str(review))
        ep['scope_class'] = 'national'
        ep['national_relevance'] = facts['national_relevance']
        ep['source'] = ', '.join(s['name'] for s in sources)
        ep['sources'], ep['fact_pack'] = sources, facts
        ep = normalize(ep)
        ep['importance_reason'] = facts.get('importance_reason') or pick.get('importance_reason', '')
        ep['review_status'] = 'source_mapped_model_review'  # not a human fact-check or a virality prediction
        ep['caption_post'] = str(ep.get('caption_post') or ep['topic']) + '\nस्रोत: ' + '; '.join(s['name'] + ' ' + s['url'] for s in sources)
        episodes.append(ep)
    return episodes
