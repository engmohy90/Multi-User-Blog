# [Multi-User-Blog](https://mohy-blog.appspot.com)

## Table of content
- [project function](#how-the-project-work)
- [consist of](#the-project-consist-of)
- [ how to run the project](#how-to-run-the-project)
- [link to the project](#links)


## How the project work 

- This project is a website where you can signup multi user.
- The signedup user can login and log out and can add posts to the mainpage also they can comment on the post of others and thier own.
- Every user can edit what he had done post or comment
- also there can likes others post 
## The project Consist of


```
multi-userblog/
├── app.yaml
├── blog.py
├── static
│   ├── css
│   │   └── main.css
│   └── images
│       ├── facebook.svg
│       ├── github.svg
│       ├── gmail.svg
│       └── linkedin.svg
└── templates
    ├── editcomment.html
    ├── edit.html
    ├── frontpage.html
    ├── html.html
    ├── login.html
    ├── mynewpost.html
    ├── myposts.html
    ├── newpost.html
    ├── post.html
    └── signup.html
```
1. static folder and contain our style for html in file main.css in css folder
- our image you can find it in images folder 

2. templates dir which contian all our html work 
3. blog.py there you can find the python code which make every thing logical and work as we plan
4. app.yaml you can treat this file as configration file for GAE 

##  how to run the project

1. clone the project on your pc
2. Install Python if necessary.
3. Install Google App Engine SDK.
4. Sign Up for a Google App Engine Account.
5. Create a new project in Google’s Developer Console using a unique name.
#### if you want to run the project offline 
- make sure you correctly install gcloud if not follow this link
- [Windows](https://drive.google.com/open?id=0Byu3UemwRffDbjd0SkdvajhIRW8278)
- [MacOS/Linux](https://drive.google.com/open?id=0Byu3UemwRffDc21qd3duLW9LMm8333)
- run this code
```
$ git clone https://github.com/engmohy90/Multi-User-Blog
$ cd to project dir
$ dev_appserver.py app.yaml
```
- now go to your browser and go to http://localhost:8080/

#### if you want to run the project online run this code 
- make sure you correctly install gcloud if not follow this link 
- [Windows](https://drive.google.com/open?id=0Byu3UemwRffDbjd0SkdvajhIRW8278)
- [MacOS/Linux](https://drive.google.com/open?id=0Byu3UemwRffDc21qd3duLW9LMm8333)
- run this code
```

$ git clone https://github.com/engmohy90/Multi-User-Blog
$ cd to project dir
$ gcloud init
$ gcloud projects create multiuserblog
$ gcloud config set project multiuserblog
$ gcloud app deploy 
$  gcloud app browse 
 ```       

## Links

- [on github](https://github.com/engmohy90/Multi-User-Blog)
- [on GAE](https://mohy-blog.appspot.com/)
