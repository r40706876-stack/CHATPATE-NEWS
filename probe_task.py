import json
import news_writer, topics
ep = news_writer.write_bulletin(topics.collect_news(None), 4)
ep["sprite"] = {"bablu": "assets/toon/bablu"}
ep["no_send"] = True
json.dump(ep, open("episodes/bulletin_test.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for l in ep["lines"]:
    print(l.get("item"), l.get("headline"), "|", l["say"], "|", l.get("stamp", ""))
