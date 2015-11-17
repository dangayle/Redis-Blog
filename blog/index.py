"""Blogging module for bottle.py, using Redis as data store."""

import os
import logging
from math import ceil
from pprint import pformat
import bottle
from bottle import BaseTemplate, Jinja2Template
from bottle import jinja2_template as template
import redis
import arrow
from faker import Factory
from slugify import slugify

log = logging.getLogger(__name__)
faker = Factory.create()
db = redis.Redis("localhost")

project_path = os.path.realpath(os.path.dirname(__file__))
template_dir = os.path.join(project_path, 'views')
bottle.TEMPLATE_PATH.insert(0, template_dir)
log.debug(template_dir)





# @bottle.route('/')
# def home():
#     return "Home"


@bottle.route('/admin')
@bottle.route('/admin/')
def admin():
    return "Admin"


@bottle.route('/admin/posts')
@bottle.route('/admin/posts/')
def admin_posts():
    return "Posts"


@bottle.route('/admin/posts/new')
@bottle.route('/admin/posts/new/')
def admin_posts_new():
    """Dummy function to create fake data."""

    title = faker.catch_phrase()
    data = {
        "id": db.incr('ids:posts'),
        "slug": slugify(title, to_lower=True),
        "published": arrow.utcnow().timestamp,
        "author": "author:1",
        "title": title,
        "content": faker.text(max_nb_chars=1000),
    }
    # for key,value in data.iteritems():
    db.hmset("post:{}".format(data['slug']), data)
    db.zadd("content:posts:live", "post:{}".format(data['slug']), data['published'])
    # db.sadd("content:posts:live", "post:{}".format(data['slug']))
    return "<pre>{}</pre>".format(db.hgetall("post:{}".format(data['slug'])))
    # return db.hset("post:{}".format(data['slug']), data)
    # return pformat(db.zrange("content:posts",0,-1))
    # return pformat(db.zadd("content:posts", data['slug'], data['published']))
    #     # if db.hset("post:{}".format(data['slug']), data):
    #     #     return "Created new post"
    #     # else:
    #     #     return "Failed"
    #     bottle.redirect("/posts/")
    # else:
    #     return "failed"


@bottle.route('/')
@bottle.route('/posts/')
@bottle.route('/posts')
def list_posts(page=1, items=10):
    """List all blog posts, in sets of 10."""

    count = db.zcard("content:posts:live")
    query_page = bottle.request.query.page or "1"
    try:
        page = int(query_page) if int(query_page) > 0 else page
    except:
        bottle.abort(404, "Page not found")
    num_pages = int(ceil(count / float(items)))
    start = page * items - items
    end = start + items - 1

    current = page * items
    previous_page = 0
    next_page = 0
    previous_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < num_pages else None
    url = bottle.request.urlparts

    pagination = {}
    for i in ("num_pages", "count", "page", "previous_page", "next_page"):
        pagination[i] = locals()[i]

    posts = (db.hgetall(x) for x in db.zrevrange("content:posts:live", start, end) if x)
    if posts:
        return template("list_posts.html", posts=posts, pagination=pagination, url=url)
    else:
        bottle.abort(404, "Nothing found")
    # return pformat([page,count,num_pages,previous_page,next_page, pagination, url])


@bottle.route('/posts/all/')
def list_all_posts():
    """List of all blog posts."""

    posts = (db.hgetall(x) for x in db.zrevrange("content:posts:live", 0, -1))
    # sys.stdout.write(pformat(posts))
    return template("list_posts.html", posts=posts)
    # return "<pre>{}</pre>".format(pformat(list(posts)))


@bottle.route('/<slug>')
@bottle.route('/<slug>/')
def get_post(slug=None):
    """Get blog post by slug."""

    post = db.hgetall("post:{}".format(slug))

    if not post:
        bottle.abort(404, "Nothing found")

    return template("post_detail.html", post=post)


@bottle.route('/static/<filepath:path>')
def serve_static(filepath):
    """Serve files from static dir."""
    return bottle.static_file(filepath, root='static')


Jinja2Template.defaults['site_title'] = "Redis Bottle Blog"
Jinja2Template.settings['filters'] = {}


def datetimeformat(value, date_format='dddd, MMM D, YYYY'):
    t = arrow.get(value)
    return t.format(date_format)
Jinja2Template.settings['filters']['datetimeformat'] = datetimeformat


def sidebar_nav():
    posts = [db.hgetall(x) for x in db.zrevrange("content:posts:live", 0, 5)]
    return posts
Jinja2Template.defaults['sidebar_nav'] = sidebar_nav


bottle.debug(True)
bottle.run(host='localhost', port=8080, reloader=True)
