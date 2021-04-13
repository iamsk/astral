import json
from collections import Counter
import requests
from vika import Vika
from benedict import benedict
from github import Github

from conf import GITHUB_TOKEN, VIKA_TOKEN, VIKA_TABLE, GITHUB_USERNAME

vika = Vika(VIKA_TOKEN)
datasheet = vika.datasheet(VIKA_TABLE, field_key="name")


def get_userid_by_name(name):
    url = 'https://api.github.com/users/{}'.format(name)
    ret = requests.get(url)
    return ret.json()['id']


def _filter(record):
    print(record['html_url'])
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
    new_ids = set(star_ids) - set(vika_star_ids)
    delete_ids = set(vika_star_ids) - set(star_ids)
    records = [_filter(star) for star in stars if star['id'] in new_ids]
    # add new stars
    datasheet.records.bulk_create(records)
    # delete un-stars
    for _id in delete_ids:
        record = datasheet.records.get(id=_id)
        record.delete()


def clean():
    vika_star_ids = [star.id for star in datasheet.records.all()]
    cl = Counter(vika_star_ids)
    for k, v in cl.items():
        if v > 1:
            print(k)
            record = datasheet.records.get(id=k)
            record.delete()


def update_from_astral():
    # export from https://app.astralapp.com/
    filename = 'astral_data_202104.json'
    data = json.load(open(filename))
    for k, v in data.items():
        repo_id = v['repo_id']
        print(repo_id)
        try:
            record = datasheet.records.get(id=repo_id)
            record.tags = ','.join([tag['name'] for tag in v['tags']])
            record.save()
        except:
            continue


save()
# update_from_astral()
