import json
import time
from collections import Counter
import requests
from retry import retry
from benedict import benedict
from vika import Vika
from github import Github

from conf import GITHUB_TOKEN, VIKA_TOKEN, VIKA_TABLE, GITHUB_USERNAME

vika = Vika(VIKA_TOKEN)
datasheet = vika.datasheet(VIKA_TABLE, field_key="name")


@retry(tries=3, delay=10, backoff=5)
def get_record(_id):
    return datasheet.records.get(id=_id)


def get_userid_by_name(name):
    url = 'https://api.github.com/users/{}'.format(name)
    ret = requests.get(url)
    return ret.json()['id']


def _filter(record):
    # print(record['html_url'])
    info = benedict(record).subset(
        keys=['name', 'description', 'html_url', 'pushed_at', 'stargazers_count', 'language',
              'id', 'created_at', 'forks_count', 'archived'])
    return info


def get_stars():
    g = Github(GITHUB_TOKEN)
    user_id = get_userid_by_name(GITHUB_USERNAME)
    print(GITHUB_USERNAME, user_id)
    user = g.get_user_by_id(user_id)
    stars = []
    for star in user.get_starred():
        try:
            stars.append(star.raw_data)
        except Exception as e:
            print(e)
            continue
    # import pdb;pdb.set_trace()
    return stars


def save():
    stars = get_stars()
    star_ids = [star['id'] for star in stars]
    vika_star_ids = [star.id for star in datasheet.records.all()]
    # add new stars
    new_ids = set(star_ids) - set(vika_star_ids)
    records = [_filter(star) for star in stars if star['id'] in new_ids]
    print('creating!')
    for i in range(0, len(records), 10):
        datasheet.records.bulk_create(records[i: i + 10])
        time.sleep(0.5)
    # delete un-stars
    print('deleting!')
    delete_ids = set(vika_star_ids) - set(star_ids)
    for _id in delete_ids:
        try:
            record = get_record(_id)
            record.update({'deleted': True})
        except:
            print(_id)
        time.sleep(0.5)
    # update repo info
    print('updating!')
    for star in stars:
        _id = star['id']
        if _id in vika_star_ids:
            dic = _filter(star)
            try:
                record = get_record(_id)
                record.update(dic)
            except:
                print(_id, dic)
            time.sleep(0.5)  # 5 requests per second limited by vika


def clean():
    vika_star_ids = [star.id for star in datasheet.records.all()]
    cl = Counter(vika_star_ids)
    for k, v in cl.items():
        if v > 1:
            print(k)
            record = get_record(k)
            record.delete()


def update_from_astral():
    # export from https://app.astralapp.com/
    filename = 'astral_data_202104.json'
    data = json.load(open(filename))
    for k, v in data.items():
        repo_id = v['repo_id']
        print(repo_id)
        try:
            record = get_record(repo_id)
            record.tags = ','.join([tag['name'] for tag in v['tags']])
            record.save()
        except:
            continue


if __name__ == '__main__':
    save()
    # update_from_astral()
