# -*- coding: utf-8 -*-

import json
import datetime
from operator import itemgetter
from collections import defaultdict
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('generate', ''))


def timestamp(value, fmt='%Y-%m-%d %H:%M'):
    return datetime.datetime.fromtimestamp(int(value)).strftime(fmt)

env.filters['timestamp'] = timestamp


def render_template(posts, chapter, chapters):
    template = env.get_template("post_template.html")
    chindices = [int(x[0]) for x in chapters]
    idx = chindices.index(int(chapter))
    return template.render(
        chapter=str(chapter),
        chapters=chapters,
        posts=sorted(posts, key=lambda p: -int(p['score'])),
        next_link=chapters[idx + 1][0] if idx < len(chapters) - 1 else "",
        previous_link=chapters[idx - 1][0] if idx > 0 else "")


def render_index(chapters):
    template = env.get_template("index.html")
    return template.render(chapters=chapters)


def create_timetable(release):
    timetable = [(int(x), int(v[0])) for x, v in release.items() if v]
    timetable = sorted(timetable)
    timetable.append((timetable[-1][0] + 1, timetable[-1][1] * 2))
    return timetable


def posts_to_timetable(posts, timetable):
    def _fits(post, idx):
        return (int(post['created_utc']) < timetable[idx + 1][1]
                and int(post['created_utc']) >= timetable[idx][1])
    result = defaultdict(list)
    cur_timetable = 0
    for post in posts:
        print(post)
        while not _fits(post, cur_timetable):
            print("not fits", timetable[cur_timetable])
            print("cur_timetable is now", cur_timetable)
            print("len(timetable) is now", len(timetable))
            cur_timetable += 1
            if cur_timetable == len(timetable) - 2:
                return result
        result[timetable[cur_timetable][0]].append(post)
    return result


def main():
    posts = []
    release = {}
    chapters = {}
    with open("filtered.json") as inf:
        posts = json.load(inf)
    with open("release.json") as inf:
        release = json.load(inf)
    with open("chapters.json") as inf:
        chapters = json.load(inf)
    print(len(posts))

    chapters = sorted(chapters.items(), key=lambda item: int(item[0]))
    posts = sorted(posts, key=itemgetter('created_utc'))
    timetable = create_timetable(release)

    posts_by_chapter = posts_to_timetable(posts, timetable)
    for chapter, post_list in posts_by_chapter.items():
        rendered = render_template(
            post_list,
            chapter,
            [x for x in chapters if int(x[0]) in posts_by_chapter.keys()])
        with open("out/{}.html".format(chapter), "w") as outf:
            outf.write(rendered)
    ch_full = [x for x in chapters if int(x[0]) in posts_by_chapter.keys()]
    ch_dicts = []
    for i in range(len(ch_full)):
        posts = posts_by_chapter[int(ch_full[i][0])]
        comments = sum(int(x["num_comments"]) for x in posts)
        ch_dicts.append({
            "number": ch_full[i][0],
            "name": ch_full[i][1],
            "timestamp": timetable[i][1],
            "posts": len(posts),
            "comments": comments
            })
    with open("out/index.html", "w") as outf:
        outf.write(render_index(ch_dicts))


if __name__ == '__main__':
    main()
