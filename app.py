from flask import Flask, request, redirect, url_for, g, render_template
from flask_mongoalchemy import MongoAlchemy
from flaskext.auth import Auth, AuthUser, login_required, logout, get_current_user_data
import datetime

app = Flask(__name__)

if "MONGO_SERVER" in os.environ:
    app.config['MONGOALCHEMY_SERVER'] = os.environ['MONGO_SERVER']
else:
    app.config['MONGOALCHEMY_SERVER'] = 'mongo'
if "MONGO_USER" in os.environ:
    app.config['MONGOALCHEMY_USER'] = os.environ['MONGO_USER']
if "MONGO_PASSWORD" in os.environ:
    app.config['MONGOALCHEMY_PASSWORD'] = os.environ['MONGO_PASSWORD']

app.config['MONGOALCHEMY_DATABASE'] = 'myflaskblog'

try:
    db = MongoAlchemy(app)
except:
    print "DATABASE CONNECTION ERROR"

auth = Auth(app, login_url_name='ulogin')


class User(db.Document):
    name = db.StringField()
    password = db.StringField()
    #encrypted = db.StringField()

class Post(db.Document):
    created = db.DateTimeField()
    title = db.StringField()
    comment = db.StringField()

class Page(db.Document):
    created = db.DateTimeField()
    title = db.StringField()
    content = db.StringField()

class Comment(db.Document):
    created = db.DateTimeField()
    comment = db.StringField()
    name = db.StringField()
    email = db.StringField()
    post_id = db.StringField()

class Blog(db.Document):
    title = db.StringField()
    subtitle = db.StringField()

class Brand(db.Document):
    brand = db.StringField()


@app.before_request
def init_users():
    # first try to get admin user if null then procee to setup
    try:
        admin = User.query.filter(User.name == 'admin').first()
    except:
        pass

    # TODO: find a way to not have this run all the time, SO SLOW!

    # if admin collection is empty need to create with default creds
    if admin is None:
        username = "admin"
        password = "password"
        auth = AuthUser(username=username)
        auth.set_and_encrypt_password(password)
        myuser = User(name=username, password=password)
        myuser.save()
        brand = Brand.query.first()
        #return render_template('setup.html', brand=brand)
        return redirect(url_for('ulogin'))
    elif admin is not None:
        authAdmin = AuthUser(username=admin.name)
        authAdmin.set_and_encrypt_password(admin.password)
        # TODO: scale users list, currently just single user mode
        g.users = {'admin': authAdmin}


def index():
    if request.method == 'POST':
        title = request.form['title']
        comment = request.form['comment']
        post = Post(created=datetime.datetime.now, title=title, comment=comment)
        post.save()

    # get posts for listing
    posts = Post.query.descending(Post.created)
    blog = Blog.query.first()
    brand = Brand.query.first()
    pages = Page.query

    # trying to get user login boolean
    user = get_current_user_data()

    return render_template('index.html', posts=posts, user=get_current_user_data(), blog=blog, brand=brand, pages=pages)

def ulogin():
    brand = Brand.query.first()
    pages = Page.query
    if request.method == 'POST':
        username = request.form['username']
        if username in g.users:
            # Authenticate and log in!
            if g.users[username].authenticate(request.form['password']):
                return redirect(url_for('admin'))
        return 'Failure :('
    return render_template('login.html', user=get_current_user_data(), brand=brand, pages=pages)

@login_required()
def admin():
    if request.method == 'POST':
        title = request.form['title']
        comment = request.form['comment']
        time = datetime.datetime.today()
        post = Post(created=time, title=title, comment=comment)
        post.save()

    # get posts for listing
    posts = Post.query.descending(Post.created)
    brand = Brand.query.first()
    blog = Blog.query.first()
    pages = Page.query
    return render_template('admin.html', posts=posts, user=get_current_user_data(), brand=brand, blog=blog, pages=pages)

#@login_required()
def ulogout():
    logout()
    return redirect(url_for('index'))

@app.route('/title', methods=['POST'])
@login_required()
def title():
    title = request.form['blogTitle']
    subtitle = request.form['blogSubTitle']
    # get title info from mongodb
    blog = Blog.query.first()
    if blog == None:
        blog = Blog(title=title, subtitle=subtitle)
    else:
        blog.title = title
        blog.subtitle = subtitle
    blog.save()
    return redirect(url_for('admin'))

@login_required()
@app.route('/setbrand', methods=['POST'])
def setbrand():
    mybrand = request.form['brand']
    brand = Brand.query.first()
    if brand == None:
        brand = Brand(brand=mybrand)
    else:
        brand.brand = mybrand
    brand.save()
    return redirect(url_for('admin'))

@login_required()
@app.route('/postremove/<id>', methods=['GET'])
def deletepost(id):
    mypost = Post.query.get(id)
    mypost.remove()
    return redirect(url_for('admin'))

@login_required()
@app.route('/postedit/<id>', methods=['GET', 'POST'])
def editpost(id):
    mypost = Post.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    # if POST then save new post data
    if request.method == 'POST':
        title = request.form['title']
        comment = request.form['comment']
        time = datetime.datetime.today()
        mypost.title = title
        mypost.comment = comment
        mypost.created = time
        mypost.save()
        return redirect(url_for('admin'))

    return render_template('postedit.html', post=mypost, user=get_current_user_data(), brand=brand, pages=pages)

@login_required()
@app.route('/pageadd', methods=['POST'])
def addpage():
    title = request.form['title']
    content = request.form['content']
    time = datetime.datetime.today()
    page = Page(created=time, title=title, content=content)
    page.save()
    return redirect(url_for('admin'))

@login_required()
@app.route('/pageremove/<id>', methods=['GET'])
def deletepage(id):
    mypage = Page.query.get(id)
    mypage.remove()
    return redirect(url_for('admin'))

@login_required()
@app.route('/pageedit/<id>', methods=['GET', 'POST'])
def editpage(id):
    mypage = Page.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    # if POST then save new post data
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        time = datetime.datetime.today()
        mypage.title = title
        mypage.content = content
        mypage.created = time
        mypage.save()
        return redirect(url_for('admin'))

    return render_template('pageedit.html', page=mypage, user=get_current_user_data(), brand=brand, pages=pages)

@login_required()
@app.route('/pages/<id>', methods=['GET'])
def viewpage(id):
    mypage = Page.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    return render_template('page.html', page=mypage, user=get_current_user_data(), brand=brand, pages=pages)

@login_required()
@app.route('/posts/<id>', methods=['GET'])
def viewpost(id):
    mypost = Post.query.get(id)
    brand = Brand.query.first()
    pages = Page.query
    comments = Comment.query.filter(Comment.post_id == id)
    return render_template('post.html', post=mypost, user=get_current_user_data(), brand=brand, pages=pages, comments=comments, ccount=comments.count())

@app.route('/setup', methods=['POST'])
def setup():
    username = request.form['username']
    password = request.form['password']
    auth = AuthUser(username=username)
    auth.set_and_encrypt_password(password)

    myuser = User(name="something")
    myuser.password = "somethingelse"
    myuser.save()

    brand = Brand.query.first()
    pages = Page.query
    #return render_template('login.html', user=get_current_user_data(), brand=brand, pages=pages)
    return redirect(url_for('ulogin'))

@login_required()
@app.route('/changepass', methods=['POST'])
def changepass():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter(User.name == username).first()
    user.password = password
    user.save()
    return redirect(url_for('admin'))

@login_required()
@app.route('/comment/<id>', methods=['GET', 'POST'])
def comment(id):
    brand = Brand.query.first()
    pages = Page.query
    if request.method == 'POST':
        comment = request.form['comment']
        name = request.form['name']
        email = request.form['email']
        time = datetime.datetime.today()
        mycomment = Comment(created=time, comment=comment, name=name, email=email, post_id=id)
        mycomment.save()
        return redirect(url_for('viewpost', id=id))

def get_comment_count(id):
    comments = Comment.query.filter(Comment.post_id == str(id))
    return comments.count()


app.add_url_rule('/', 'index', index, methods=['GET', 'POST'])
app.add_url_rule('/admin/', 'admin', admin, methods=['GET', 'POST'])
app.add_url_rule('/logout/', 'ulogout', ulogout)
app.add_url_rule('/login/', 'ulogin', ulogin, methods=['GET', 'POST'])

app.secret_key = 'N4BUdSXUzHxNoO8g'

if __name__ == '__main__':
    app.jinja_env.globals.update(get_comment_count=get_comment_count)
    app.run(debug=True,host='0.0.0.0')
