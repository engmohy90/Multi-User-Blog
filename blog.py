import webapp2
import jinja2
import os
import hmac
import re
from google.appengine.ext import db
import string
import random
import hashlib

temp_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(temp_dir),
 autoescape = True)

secret  = "mohy"

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(u):
	return USER_RE.match(u)
PASSWORD_RE = re.compile("^.{3,20}$")
def valid_password(p):
	return PASSWORD_RE.match(p)
EMAIL_RE = re.compile("^[\S]+@[\S]+.[\S]+$")
def valid_email(e):
	return EMAIL_RE.match(e)

def hmac_secure(h):
	h = str(h)
	x = (hmac.new(secret,h)).hexdigest()
	y = "%s|%s" %(h, x)
	return y
def secure_cookie(h):
	z = h.split("|")[0]
	if h == hmac_secure(z):
		return z
	else:
		return None

def make_pw_hash(pw):
	salt = ''.join(random.choice(string.letters) for x in xrange(5))
	pw = str(pw)
	h = hashlib.sha256(pw+salt).hexdigest()
	return "%s|%s"%(h,salt)
def pass_check_salt(pw,h):
	salt = h.split("|")[1]
	hash_p = hashlib.sha256(pw+salt).hexdigest()
	if hash_p == h.split("|")[0] :
		return True
	else:
		return False

class Users(db.Model):

	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty()
	created = db.DateTimeProperty(auto_now = True)

class Post(db.Model):

	title = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	username =db.StringProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	last_modified = db.DateTimeProperty(auto_now = True)


		
class Handler(webapp2.RequestHandler):

	def write(self, *a, **kw):

		self.response.out.write(*a, **kw)
	
	def render_str(self, template, **params):
		
		t = jinja_env.get_template(template)
		return t.render(params)

	def render_html(self, template, **kw):
		
		self.write(self.render_str(template, **kw))


class MainPage(Handler):


	def get(self):
		user = ""
		user_id = self.request.cookies.get("user_id", "1234|6547")
		check_cookie = secure_cookie(user_id)
		if check_cookie :
			user_name = Users.get_by_id(int(check_cookie),parent=None)
			user = user_name.username
			self.render_html("frontpage.html", user = user)
		else:
			
			self.render_html("frontpage.html", user = user)



class LogIn(Handler):

	def get(self):
		self.render_html("login.html")

	def post(self):
		real_pass = "|"
		username = self.request.get("username")
		password = self.request.get("password")

		user_pass = db.GqlQuery("SELECT * FROM Users WHERE username='%s'" % username)
		user_pass_get = user_pass.get()
		if user_pass_get :
			real_pass = pass_check_salt(password, user_pass_get.password)
		if real_pass == True :
			id_hashed = hmac_secure(user_pass_get.key().id())
			self.response.headers.add_header("set-Cookie","user_id=%s" %id_hashed)
			self.redirect("/")

		else:
			self.render_html("login.html", error = "user name and password are not correct")
		
class SignUp(Handler):
	
	def get(self):
		
		self.render_html("signup.html")
		
	def post(self):
		have_error = False
		username = self.request.get("username")
		password = self.request.get("password")
		verify = self.request.get("verify")
		email = self.request.get("email")
		
		error = {'username':username, 'email':email}
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
		check_username = db.GqlQuery("SELECT * from Users WHERE username='%s'"%username)
		ge_ch=check_username.get()
		if ge_ch :
			error["exist"] = "user already exist try an other user"
			have_error = True
		if have_error == True :
			
			self.render_html("signup.html", **error)

		else :
			has_password = make_pw_hash(password)
			save_entity = Users(username = username, password = has_password, email = email)
			save_entity.put()
			
			user_id = save_entity.key().id()
			id_hashed = hmac_secure(user_id)
			self.response.headers.add_header("set-Cookie","user_id=%s" % id_hashed)
			self.redirect("/welcome")

class Welcome(Handler):
	def get(self):
		user_id = self.request.cookies.get("user_id", "1234|6547")
		check_cookie = secure_cookie(user_id)
		if check_cookie :
			user_name = Users.get_by_id(int(user_id.split("|")[0]),parent=None)
			self.write("welcome %s " % user_name.username)
		else:
			self.render_html("signup.html")

class NewPost(Handler):
	def get(self):

		cookie_get = self.request.cookies.get("user_id", "1234|6547")
		check_cookie = secure_cookie(cookie_get)
		if check_cookie == None:
			self.render_html("newpost.html" ,login="please login first")
		else:
			self.render_html("newpost.html")
	def post(self):
		cookie_get = self.request.cookies.get("user_id", "1234|6547")
		check_cookie = secure_cookie(cookie_get)
		title = self.request.get("title")
		content = self.request.get("content")
		error = dict()
		have_error =False
		if not title :
			error["title_empty"] = "please enter title"
			have_error = True
		if not content :
			error["post_empty"] = "please enter content to your post"
			have_error = True
		if check_cookie == None:
			have_error = True
			error["login"] = "please login first"
		if have_error == False:
			username = Users.get_by_id(int(check_cookie), parent=None)
			q = Post(title = title, content = content, username=username.username)
			q.put()
			self.redirect("/mynewpost/%s"%str(q.key().id()))
		else:
			self.render_html("newpost.html", **error)

class MyNewPost(Handler):

	def get(self,i):
		post = Post.get_by_id(int(i))
		title = post.title
		con = post.content
		content = con.replace("\n","<br>")
		self.render_html("mynewpost.html", title = title, content = content)

class MyPosts(Handler):
	
	def get(self):
		cookie_get = self.request.cookies.get("user_id", "1234|6547")
		user_id = secure_cookie(cookie_get)
		if user_id :
			user_n = Users.get_by_id(int(user_id))
			user_name = user_n.username
			posts = db.GqlQuery("SELECT * FROM Post WHERE username = '%s'"%user_name)
			self.render_html("myposts.html", posts = posts)
		else:
			self.redirect("/login")


class LogOut(Handler):

	def get(self):
		self.response.headers.add_header("set-Cookie","user_id=; path=/")
		self.redirect("/")
						
app =  webapp2.WSGIApplication([("/", MainPage), ("/login", LogIn), ("/signup", SignUp), ("/welcome", Welcome),
	("/logout", LogOut), ("/newpost", NewPost), ("/myposts", MyPosts), ("/mynewpost/([0-9]+)", MyNewPost)]
	,debug = True)
