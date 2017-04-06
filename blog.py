import webapp2
import jinja2
import os
import hmac
import re
from google.appengine.ext import ndb
import string
import random
import hashlib


temp_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(temp_dir),
                               autoescape=True)
secret = "mohy"
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")


# check username match the regular exp
def valid_username(u):
    return USER_RE.match(u)
PASSWORD_RE = re.compile("^.{3,20}$")


# check password match the regular exp
def valid_password(p):
    return PASSWORD_RE.match(p)
EMAIL_RE = re.compile("^[\S]+@[\S]+.[\S]+$")


# check email match the regular exp
def valid_email(e):
    return EMAIL_RE.match(e)


# hashing the cookies
def hmac_secure(h):
    h = str(h)
    x = (hmac.new(secret, h)).hexdigest()
    y = "%s|%s" % (h, x)
    return y


# check if cookie exist
def secure_cookie(h):
    z = h.split("|")[0]
    if h == hmac_secure(z):
        return z
    else:
        return None


# hashing the password for safe store at db
def make_pw_hash(pw):
    salt = ''.join(random.choice(string.letters) for x in xrange(5))
    pw = str(pw)
    h = hashlib.sha256(pw+salt).hexdigest()
    return "%s|%s" % (h, salt)


# check if password as we hased in our db
def pass_check_salt(pw, h):
    salt = h.split("|")[1]
    hash_p = hashlib.sha256(pw+salt).hexdigest()
    if hash_p == h.split("|")[0]:
        return True
    else:
        return False


# orender python code in templet
def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


# making db for usernames of our blog
class Users(ndb.Model):

    username = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    created = ndb.DateTimeProperty(auto_now=True)


# making db for comment with same post id to link post with comment
class Comment(ndb.Model):

    c_username = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    post_id = ndb.IntegerProperty(required=True)
    comment = ndb.TextProperty(required=True)


# make db for post with same username as login to like user with post
class Post(ndb.Model):

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
        return render_str("post.html", data=post, comments=comments)


# easy render python code in templete and write the html code 
class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):

        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):

        t = jinja_env.get_template(template)
        return t.render(params)

    def render_html(self, template, **kw):

        self.write(self.render_str(template, **kw))

    # save likes in db also check if illegibility for makeing like
    def like_post(self, like, login_id):

        post_query = Post.get_by_id(int(like))
        login_query = Users.get_by_id(int(login_id))
        u = login_query.username
        if u == post_query.username:
            error = "this is your post"
            return error

        if u in post_query.like:
            error = "you liked this before"
            return error
        if u in post_query.unlike:
            list_unlike = post_query.unlike
            list_unlike.remove(u)
            post_query.unlike = list_unlike
            post_query.nunlike = post_query.nunlike - 1

        if post_query.like:

            post_query.like = post_query.like + [u]
            post_query.nlike = post_query.nlike + 1
            post_query.put()
            return self.redirect("/")
        else:
            post_query.like = [u]
            post_query.nlike = 1
            post_query.put()
            return self.redirect("/")

    # save unlikes in db also check if illegibility for makeing unlike
    def unlike_post(self, unlike, login_id):

        post_query = Post.get_by_id(int(unlike))
        login_query = Users.get_by_id(int(login_id))
        u = login_query.username
        if u == post_query.username:
            error = "this is your post"
            return error
        if u in post_query.unlike:
            error = "you unliked this before"
            return error
        if u in post_query.like:
            list_like = post_query.like
            list_like.remove(u)
            post_query.like = list_like
            post_query.nlike = post_query.nlike - 1
        if post_query.unlike:
            post_query.unlike = post_query.unlike + [u]
            post_query.nunlike = post_query.nunlike + 1
            post_query.put()
            return self.redirect("/")
        else:
            post_query.unlike = [u]
            post_query.nunlike = 1
            post_query.put()
            return self.redirect("/")

    # delete post from db
    def del_post(self, key_id, cookies):
        key_id = int(key_id)
        x = Post.get_by_id(key_id)
        user_id = secure_cookie(cookies)
        if not user_id:
            return self.redirect("/login")
        user_n = Users.get_by_id(int(user_id))
        user_name = user_n.username
        if x.username == user_name:
            x.key.delete()
            error = "post deleted"
            return error
        else:
            error = "this post belong to %s you cannot delete" % x.username
            return error

    def edit_post(self, key_id, cookies):
        key_id = int(key_id)
        x = Post.get_by_id(key_id)
        user_id = secure_cookie(cookies)
        if not user_id:
            return self.redirect("/login")
        user_n = Users.get_by_id(int(user_id))
        user_name = user_n.username
        if not user_name == x.username:
            error = " this  post does not belong to you"
            return error


# mainpage which contain 10 latest created post
class MainPage(Handler):

    def get(self):
        posts = Post.query().order(-Post.created).fetch(10)
        user = ""
        user_id = self.request.cookies.get("user_id", "1234|6547")
        check_cookie = secure_cookie(user_id)
        if check_cookie:
            user_name = Users.get_by_id(int(check_cookie))
            user = user_name.username
            self.render_html("frontpage.html", user=user, posts=posts)
        else:

            self.render_html("frontpage.html", user=user, posts=posts)

    # check which button clicked (like or edite or deleted or..) and
    # make right dession 
    def post(self):
        comdel = self.request.get("comdel")
        comedit = self.request.get("comedit")
        comment = self.request.get("comment")
        postcom_id = self.request.get("post_id")
        del_key = self.request.get("del")
        edit_key = self.request.get("edit")
        like = self.request.get("like")
        unlike = self.request.get("unlike")
        my_cookie = self.request.cookies.get("user_id", "1234|6547")
        login_id = secure_cookie(my_cookie)
        posts = Post.query().order(-Post.created).fetch(10)
        user = ""
        if login_id:
            user_name = Users.get_by_id(int(login_id))
            user = user_name.username

        if del_key:
            del_result = self.del_post(del_key, my_cookie)
            self.render_html("frontpage.html", user=user, posts=posts,
                             error=del_result)
        if edit_key:
            edit_result = self.edit_post(edit_key, my_cookie)
            if edit_result:
                self.render_html("frontpage.html", user=user, posts=posts,
                                 error=edit_result)
            else:
                self.redirect("/edit?key=%s" % edit_key)
        if unlike:
            unlike_click = None
            if login_id:
                unlike_click = self.unlike_post(unlike, login_id)
            if unlike_click is not None:
                self.render_html("frontpage.html", user=user,
                                 posts=posts, error=unlike_click)
            else:
                self.redirect("/login")

        if like:
            like_click = None
            if login_id:
                like_click = self.like_post(like, login_id)
            if like_click is not None:
                self.render_html("frontpage.html", user=user, posts=posts,
                                 error=like_click)
            else:
                self.redirect("/login")

        if postcom_id:
            if login_id:
                c_username = Users.get_by_id(int(login_id))
                q = Comment(comment=comment, post_id=int(postcom_id),
                            c_username=c_username.username)
                q.put()
                self.redirect("/")

            else:
                self.redirect("/login")
        if comdel:
            coment_q = Comment.get_by_id(int(comdel))
            if coment_q.c_username == user:
                coment_q.key.delete()
                self.render_html("frontpage.html", user=user, posts=posts)
            else:
                self.render_html("frontpage.html", user=user, posts=posts,
                                 error="you cannot delete this comment")
        if comedit:
            coment_q = Comment.get_by_id(int(comedit))
            if coment_q.c_username == user:
                self.redirect("/comedit?id=%s" % coment_q.key.id())
            else:
                self.render_html("frontpage.html", user=user, posts=posts,
                                 error="you cannot edite this comment")


# check for user then add cookies if user is ok
class LogIn(Handler):

    def get(self):
        self.render_html("login.html")

    def post(self):
        real_pass = "|"
        username = self.request.get("username")
        password = self.request.get("password")

        user_pass = ndb.gql("SELECT * FROM Users WHERE username='%s'"
                            % username)
        user_pass_get = user_pass.get()
        if user_pass_get:
            real_pass = pass_check_salt(password, user_pass_get.password)
        if real_pass is True:
            id_hashed = hmac_secure(user_pass_get.key.id())
            self.response.headers.add_header("set-Cookie", "user_id=%s"
                                             % id_hashed)
            self.redirect("/")

        else:
            self.render_html("login.html",
                             error="user name and password are not correct")


# store new user in our db
class SignUp(Handler):

    def get(self):

        self.render_html("signup.html")

    def post(self):
        have_error = False
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")
        error = {'username': username, 'email': email}
        if not valid_username(username):
            error["er_user"] = "user name have error"
            have_error = True
        if not valid_password(password):
            error["er_paa"] = "password error"
            have_error = True
        elif password != verify:
            error["er_ver"] = "password not match"
            have_error = True
        if not valid_email(email):
            error["er_email"] = "email error"
        check_username = ndb.gql("SELECT * from Users WHERE username='%s'"
                                 % username)
        ge_ch = check_username.get()
        if ge_ch:
            error["exist"] = "user already exist try an other user"
            have_error = True
        if have_error is True:

            self.render_html("signup.html", **error)

        else:
            has_password = make_pw_hash(password)
            save_entity = Users(username=username, password=has_password,
                                email=email)
            save_entity.put()
            user_id = save_entity.key.id()
            id_hashed = hmac_secure(user_id)
            self.response.headers.add_header("set-Cookie", "user_id=%s"
                                             % id_hashed)
            self.redirect("/welcome")


# wellcome for new user
class Welcome(Handler):

    def get(self):
        user_id = self.request.cookies.get("user_id", "1234|6547")
        check_cookie = secure_cookie(user_id)
        if check_cookie:
            user_name = Users.get_by_id(int(user_id.split("|")[0]))
            self.write("welcome %s " % user_name.username)
        else:
            self.render_html("signup.html")


# adding new post to our db by username
class NewPost(Handler):

    def get(self):

        cookie_get = self.request.cookies.get("user_id", "1234|6547")
        check_cookie = secure_cookie(cookie_get)
        if check_cookie is None:
            self.redirect("/login")
        else:
            self.render_html("newpost.html")

    def post(self):
        cookie_get = self.request.cookies.get("user_id", "1234|6547")
        check_cookie = secure_cookie(cookie_get)
        title = self.request.get("title")
        content = self.request.get("content")
        error = dict()
        have_error = False
        if not title:
            error["title_empty"] = "please enter title"
            have_error = True
        if not content:
            error["post_empty"] = "please enter content to your post"
            have_error = True
        if check_cookie is None:
            have_error = True
            error["login"] = "please login first"
        if have_error is False:
            username = Users.get_by_id(int(check_cookie))
            q = Post(title=title, content=content, username=username.username,
                     nlike=0, nunlike=0)
            q.put()
            self.redirect("/mynewpost/%s" % str(q.key.id()))
        else:
            self.render_html("newpost.html", **error)


# view post alone t
class MyNewPost(Handler):

    def get(self, i):

        post = Post.get_by_id(int(i))
        title = post.title
        con = post.content
        content = con.replace("\n", "<br>")
        self.render_html("mynewpost.html", title=title, content=content)


# view only the login user posts
class MyPosts(Handler):

    def get(self):
        cookie_get = self.request.cookies.get("user_id", "1234|6547")
        user_id = secure_cookie(cookie_get)
        if user_id:
            user_n = Users.get_by_id(int(user_id))
            user_name = user_n.username
            posts = ndb.gql("SELECT * FROM Post WHERE username='%s'"
                            % user_name)
            self.render_html("myposts.html", posts=posts)
        else:
            self.redirect("/login")

    def post(self):
        del_key = self.request.get("del")
        edit_key = self.request.get("edit")
        my_cookie = self.request.cookies.get("user_id", "1234|6547")
        if del_key:
            del_result = del_post(del_key, my_cookie)
            self.write(del_result)
        if edit_key:
            edit_result = edit_post(edit_key, my_cookie)
            if edit_result:
                self.write(edit_result)
            else:
                self.redirect("/edit?key=%s" % edit_key)


# clear cookies and logout
class LogOut(Handler):

    def get(self):
        self.response.headers.add_header("set-Cookie", "user_id=; path=/")
        self.redirect("/signup")


# edit post 
class Edit(Handler):

    def get(self):
        referer = self.request.headers['Referer']
        key = self.request.get("key")
        if key:
            post = Post.get_by_id(int(key))
            self.render_html("edit.html", title=post.title,
                             content=post.content, back=referer)
        else:
            self.write("error happend ")

    def post(self):

        cancle = self.request.get("cancle")
        key = self.request.get("key")
        cookie_get = self.request.cookies.get("user_id", "1234|6547")
        check_cookie = secure_cookie(cookie_get)
        title = self.request.get("title")
        content = self.request.get("content")
        error = dict()
        have_error = False
        if cancle:
            self.redirect(str(cancle))
        if not title:
            error["title_empty"] = "please enter title"
            have_error = True
        if not content:
            error["post_empty"] = "please enter content to your post"
            have_error = True
        if check_cookie is None:
            have_error = True
            error["login"] = "please login first"
        if have_error is False and not cancle:
            username = Users.get_by_id(int(check_cookie))
            q = Post.get_by_id(int(key))
            q.title = title
            q.content = content
            q.put()
            self.redirect("/mynewpost/%s" % str(q.key.id()))
        else:
            self.render_html("edit.html", **error)


# edit comment of the posts
class Comedit(Handler):

    def get(self):
        comment_id = self.request.get("id")
        coment_q = Comment.get_by_id(int(comment_id))
        self.render_html("editcomment.html", comedit=coment_q)

    def post(self):
        comment = self.request.get("comment")
        comedit = self.request.get("comedit")
        cancle = self.request.get("cancle")
        my_cookie = self.request.cookies.get("user_id", "1234|6547")
        login_id = secure_cookie(my_cookie)
        user = ""
        if login_id:
            user_name = Users.get_by_id(int(login_id))
            user = user_name.username
        if comedit:
            coment_q = Comment.get_by_id(int(comedit))
            if user == coment_q.c_username:
                coment_q.comment = comment
                coment_q.put()
                self.redirect("/")
        else:
            self.redirect("/")


app = webapp2.WSGIApplication([("/", MainPage),
                               ("/login", LogIn),
                               ("/signup", SignUp),
                               ("/welcome", Welcome),
                               ("/logout", LogOut),
                               ("/newpost", NewPost),
                               ("/myposts", MyPosts),
                               ("/mynewpost/([0-9]+)", MyNewPost),
                               ("/edit", Edit),
                               ("/comedit", Comedit)
                               ], debug=True)
