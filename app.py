from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug import secure_filename
import os
import json
from datetime import datetime


with open('config.json', 'r') as c:
    params = json.load(c)["params"]


app = Flask(__name__)
app.secret_key="super-secret-key"
app.config["UPLOAD_FOLDER"]=params["uploader_location"]
local_server = True
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-pass']
)
mail = Mail(app)


db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tline=db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    return render_template('index.html', params=params, posts=posts)


@app.route("/edit/<string:sno>" ,methods=["GET","POST"])
def edit(sno):
    if ("user" in session and session["user"]== params["admin-user"]) :
        if request.method== "POST":
            title=request.form.get("title")
            tline=request.form.get("tline")
            slug=request.form.get("slug")
            content=request.form.get("content")
            image=request.form.get("img_file")
            date=datetime.now()

            if sno == "0" :
                post=Posts(title=title, slug=slug, content=content, img_file=image, date=date, tline=tline)
                db.session.add(post)
                db.session.commit()

            else:
                post=Post.query.filter_by(sno=sno).first()
                post.title=title
                post.slug=slug
                post.content=content
                post.img_file=file
                post.tline=tline
                post.date=date
                db.session.commit()

        post=Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", post=post, params=params )


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/login")

@app.route("/uploader", methods=['GET' ,'POST'])
def uploader():
    if 'user' in session and session['user']== params['admin-user'] :
        if request.method == 'POST':
            f=request.files['files']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Upload Successfully"

@app.route("/login", methods=['GET', 'POST'])
def login():
    if("user" in session and session["user"]== params["admin-user"]):
        posts=Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method=="POST":
        uname=request.form.get("uname")
        upass=request.form.get("upass")
        if(uname== params["admin-user"] and upass== params["admin-pass"]):
            session["user"]=uname
            posts=Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

    else:
        return render_template('login.html', params=params,)


@app.route("/delete/<string:sno>")
def delete(sno):
    if("user" in session and session["user"]== params["admin-user"]):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/login")


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + phone
                          )
    return render_template('contact.html', params=params)


app.run(debug=True)
