from flask import Flask, request, redirect, url_for, g, render_template
from flask.ext.mongoalchemy import MongoAlchemy
from flaskext.auth import Auth, AuthUser, login_required, logout, get_current_user_data
import datetime

app = Flask(__name__)

app.config['MONGOALCHEMY_DATABASE'] = 'myflaskblog'
app.config['MONGOALCHEMY_SERVER'] = 'mongo.bashtothefuture.com'
db = MongoAlchemy(app)

auth = Auth(app, login_url_name='ulogin')


class User(db.Document):
    name = db.StringField()
    password = db.StringField()

class Post(db.Document):
    created = db.DateTimeField()
    title = db.StringField()
    comment = db.StringField()

class Page(db.Document):
    created = db.DateTimeField()
    title = db.StringField()
    content = db.StringField()

class Blog(db.Document):
    title = db.StringField()
    subtitle = db.StringField()

class Brand(db.Document):
    brand = db.StringField()


@app.before_request
def init_users():
    admin = User.query.filter(User.name == 'admin').first()
    authAdmin = AuthUser(username=admin.name, password=admin.password)
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


app.add_url_rule('/', 'index', index, methods=['GET', 'POST'])
app.add_url_rule('/admin/', 'admin', admin, methods=['GET', 'POST'])
app.add_url_rule('/logout/', 'ulogout', ulogout)
app.add_url_rule('/login/', 'ulogin', ulogin, methods=['GET', 'POST'])

app.secret_key = 'N4BUdSXUzHxNoO8g'

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
