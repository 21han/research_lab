# User

#### Three sample users in current user database:

* email: 123@123.com password:123
* email: michael@google.com  password:123
* email: admin@backtesting.com password: admin

(feel free to create more through register page)


####To enforce a user to access web page after login 

Add login_require decorator under the endpoint route
```sh
@login_required
```
(eg. /home /account)

####To get a current user's info
use object: current_user

for example, after user Michael log in
```sh
print(current_user)
>>> User('3', 'Michael', 'michael@google.com', 'default.jpg')
print(current_user.id)
>>> 3
print(current_user.username)
>>> Michael
print(current_user.email)
>>> michael@google.com
print(current_user.image_file)
>>> 'default.jpg'
```

####To add more attributes to User object
line 213 -line 223

```python
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    # strategy = db.relationship('Strategy', backref='location', lazy=True)
    def __repr__(self):
        # return f"User('{self.username}', '{self.email}', '{self.image_file}')"
        return f"User('{self.id}', '{self.username}', '{self.email}', '{self.image_file}')"
```

#####Update column(s) in user table with matched data type