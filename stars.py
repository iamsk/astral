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
    info = benedict(record).subset(
        keys=['name', 'description', 'html_url', 'updated_at', 'stargazers_count', 'language',
              'id', 'created_at', 'forks_count'])
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


save()
