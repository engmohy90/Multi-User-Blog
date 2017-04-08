from google.appengine.ext import ndb


class Users(ndb.Model):
    """ making db for usernames of our blog """

    username = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now=True)


class Comment(ndb.Model):
    """ making db for comment with same post id to link post with comment"""

    c_username = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    post_id = ndb.IntegerProperty(required=True)
    comment = ndb.TextProperty(required=True)


class Post(ndb.Model):
    """make db for post with same username as login to like user with post """

    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    username = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    like = ndb.StringProperty(repeated=True)
    unlike = ndb.StringProperty(repeated=True)
    nunlike = ndb.IntegerProperty()
    nlike = ndb.IntegerProperty()

# search for coment via post id
    def render_post(post):
        post_id = post.key.id()
        comments = ndb.gql("SELECT * FROM Comment WHERE post_id=%d"
                           % post_id).fetch()
        return comments
