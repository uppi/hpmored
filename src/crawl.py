# -*- coding: utf-8 -*-

import time
import datetime
import traceback
import requests
import json
import re
from lxml import html
from collections import defaultdict

FIRST_CHAPTER = 76


def get_subreddit_search_url(subreddit, from_timestamp, to_timestamp):
    return ("http://reddit.com/search.json?q=(and+subreddit%3A'{}'"
            "+timestamp%3A{}..{})&syntax=cloudsearch&limit=100".format(
                subreddit, from_timestamp, to_timestamp))


def search_response(from_timestamp, to_timestamp):
    url = get_subreddit_search_url('hpmor', from_timestamp, to_timestamp)
    print("Searching", url)
    headers = {'User-Agent': 'Python:HPMORED crawler v. 0.1 (by /u/upppi)'}
    response = requests.get(url, headers=headers)
    result = response.json()
    return result


def unix_timestamp(dt):
    return int(time.mktime(dt.timetuple()))


def crawl_reddit(from_datetime, to_datetime):
    DAY = 86400
    day_count = 10
    results = []
    ts = unix_timestamp(from_datetime)
    finish = unix_timestamp(to_datetime)
    just_reduced = False
    while(ts < finish):
        print("current timestamp is {}, {} days to finish".format(
            ts, (finish-ts)/DAY))
        ts2 = int(ts + DAY * day_count)
        response = search_response(ts, ts2)
        try:
            posts = response['data']['children']
            print("Found {} posts".format(len(posts)))
            if len(posts) < 100:  # 100 is API limit -> reduce search period
                results += posts
                ts = ts2
                print("Saved.")
                if len(posts) < 10 and not just_reduced:
                    day_count = day_count * 2
                    print("day_count increased to {}".format(day_count))
                just_reduced = False
            else:
                day_count = day_count / 2
                print("day_count reduced to {}".format(day_count))
                just_reduced = True
        except:
            ts = ts2
            print("{}-{} caused an error".format(ts, ts2))
            traceback.print_exc()
        time.sleep(2)  # Make no more than thirty requests per minute.
        # According to https://github.com/reddit/reddit/wiki/API#rules
    return results


def filter_fields(posts):
    FIELDS = ['title', 'url', 'num_comments',
              'permalink', 'author', 'score', 'created_utc']
    filtered = [{f: x['data'].get(f) for f in FIELDS} for x in posts]
    return filtered


def create_release(filtered, last_chapter):
    simple = {f['created_utc']: f['title'] for f in filtered}
    grouped = defaultdict(list)
    for x in sorted(simple):
        m = re.search(r'([0-9][0-9][0-9]?)', simple[x])
        if m and 'Following the Phoenix' not in simple[x]:
            chapter = int(m.groups(1)[0])
            if chapter > FIRST_CHAPTER and chapter <= last_chapter:
                grouped[chapter].append((x, simple[x]))
    release = {x: grouped[x][0] if grouped[x] else None for x in grouped}
    release[78] = None
    release[79] = None
    release[90] = grouped[90][3]
    release[93] = grouped[93][1]
    release[95] = grouped[95][2]
    release[99] = None
    release[100] = None
    release[101] = grouped[99][1]
    release[104] = grouped[104][1]
    release[105] = grouped[105][1]
    release[109] = grouped[109][2]
    release[110] = grouped[110][1]
    release[111] = grouped[111][1]
    release[112] = grouped[112][1]
    release[114] = grouped[114][8]
    release[117] = grouped[117][1]
    release[118] = grouped[118][1]
    return release


def get_chapters():
    page = requests.get("http://hpmor.com")
    tree = html.fromstring(page.text)
    chapters = [s.strip()
                for s in tree.xpath("//ul[@class='toclist']/li/a/text()")]
    return chapters


def main():
    from_datetime = datetime.date(2011, 11, 29)
    to_datetime = datetime.datetime.now()
    results = crawl_reddit(from_datetime, to_datetime)
    filtered = filter_fields(results)
    with open("filtered.json", "w") as outf:
        json.dump(filtered, outf)
    chapters = get_chapters()
    chapters_dict = dict((idx + 1, name) for idx, name in enumerate(chapters))
    with open("chapters.json", "w") as outf:
        json.dump(chapters_dict, outf)
    release = create_release(filtered, last_chapter=len(chapters) + 1)
    with open("release.json", "w") as outf:
        json.dump(release, outf)


def create_only_release():
    with open("filtered.json") as inf:
        filtered = json.load(inf)
    with open("chapters.json") as inf:
        chapters = json.load(inf)
    release = create_release(filtered, last_chapter=len(chapters) + 1)
    with open("release.json", "w") as outf:
        json.dump(release, outf)


if __name__ == '__main__':
    create_only_release()
