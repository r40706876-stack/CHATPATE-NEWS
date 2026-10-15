import collections, topics
c = topics.collect_news()
cnt = collections.Counter(k["cat"] for k in c["kaam"])
out = [f"कुल {len(c['kaam'])} खबरें, हाल के विषय: {c['recent_cats']}"] + [f"{k}: {v}" for k, v in cnt.items()]
out += [f"[{k['cat']}] {k['trend']}" for k in c["kaam"]]
open("viral_test.txt", "w").write("\n".join(out)); print("\n".join(out))
