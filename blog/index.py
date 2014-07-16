"""Blogging module for bottle.py, using Redis as data store."""
import sys
import os
from math import ceil
from pprint import pformat
import bottle
from bottle import BaseTemplate
from bottle import jinja2_view as view
from bottle import jinja2_template as template
import redis
import arrow
from faker import Factory
from slugify import slugify
from collections import namedtuple

faker = Factory.create()
db = redis.Redis("localhost")
# PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))


BaseTemplate.defaults['site_title'] = "Blog"


@bottle.route('/')
def home():
    return "Home"


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
    previous = 0
    next = 0
    previous = page - 1 if page > 1 else None
    next = page + 1 if page < num_pages else None
    url = bottle.request.urlparts

    pagination = {}
    for i in ("num_pages", "count", "page", "previous", "next"):
        pagination[i] = locals()[i]

    posts = [db.hgetall(x) for x in db.zrange("content:posts:live", start, end) if x]
    if posts:
        return template("list_posts.html", posts=posts, pagination=pagination, url=url)
    else:
        bottle.abort(404, "Nothing found")
    # return pformat([page,count,num_pages,previous,next, pagination, url])
    # [1, 20, 2, None, 2, {'count': 20, 'next': 2, 'num_pages': 2, 'page': 1, 'previous': None}, SplitResult(scheme='http', netloc='localhost:8080', path='/posts', query='page=1', fragment='')]


@bottle.route('/posts/all/')
def list_all_posts():
    """List of all blog posts."""

    posts = (db.hgetall(x) for x in db.zrange("content:posts", 0, -1))
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

    return template("<h1>{{post['title']}}</h1>\n<div>{{post['content']}}</div>", post=post)


@bottle.route('/static/<filepath:path>')
def serve_static(filepath):
    """Serve files from static dir."""
    return bottle.static_file(filepath, root='static')


# bottle.TEMPLATE_PATH.insert(0, '../views/')
bottle.debug(True)
bottle.run(host='localhost', port=8080, reloader=True)
