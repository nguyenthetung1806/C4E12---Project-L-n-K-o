from flask import Flask, render_template, request, redirect, session
from passlib.hash import sha256_crypt
import mlab
from base64 import b64encode
from bson.objectid import ObjectId
from mongoengine import *


app = Flask(__name__)
app.config["SECRET_KEY"] = "piudfpasudfpa7wr09 21y"

mlab.connect()

class Account(Document):
    username = StringField()
    name = StringField()
    image = StringField()
    password = StringField()
    email = EmailField()
    phone = StringField()
    #friend system
    friendlist = ListField()
    friend_request_sent = ListField()
    friend_accept_pending = ListField()
    #
    #bet system
    pending_bet = ListField()
    active_bet = ListField()
    win_bet = ListField()
    lost_bet = ListField()








@app.route('/')
def index():
    return render_template('homepage.html')


@app.route('/signup',methods=['GET','POST'])
def signup():
    if request.method == "GET":
        return render_template('signup.html')
    elif request.method == "POST":
        form = request.form
        username = form['username']
        password = sha256_crypt.encrypt(form['password'])
        name = form['name']
        email = form['email']
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist:
            account = None
        if account is None:
            account = Account(name=name, password=password, username=username, email=email)
            account.save()
            return redirect('/login')
        else:
            message = "Tên đăng nhập đã tồn tại, vui lòng chọn tên khác"
            return render_template('message.html', message = message)



@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')
    elif request.method == "POST":
        form = request.form
        username = form['username']
        password = form['password']
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist:
            account = None
        if account is None:
            message = "Tài khoản không tồn tại"
            return render_template('message.html', message = message)
        else:
            if sha256_crypt.verify(password, account.password) == True:
                session["username"] = account.username
                url = "/profile/" + account.username
                return redirect(url)
            else:
                message = "Sai mật khẩu"
                return render_template('message.html', message = message)




@app.route('/profile/<username_url>', methods=['GET','POST'])
def profile(username_url):
    username = session['username']
    username_url = username_url
    account = Account.objects.get(username = username)
    account_other = Account.objects.get(username = username_url)
    bets_to_show = []
    for bet in account_other.active_bet:
        bets_to_show.append(Contract_type_1.objects().with_id(bet))

    # dùng để nhét các document player tham gia kèo vào player_to_show []
    player_usernames = []
    for element in bets_to_show:
        for name_user in element.party_left:
            if name_user not in player_usernames:
                player_usernames.append(name_user)
        for name_user in element.party_right:
            if name_user not in player_usernames:
                player_usernames.append(name_user)
    players_to_show = []
    for username_each in player_usernames:
            players_to_show.append(Account.objects.get(username = username_each))
    # xong

    return render_template('profile.html',  account = account,
                                            account_other = account_other,
                                            username = username,
                                            username_url = username_url,
                                            bets_to_show = bets_to_show,
                                            players_to_show = players_to_show)












@app.route('/edit.profile/<username_url>', methods=['GET','POST'])
def edit_profile(username_url):
    account = Account.objects.get(username = username_url)
    if request.method == "GET":
        return render_template('edit_profile.html', account = account)
    elif request.method == "POST":
        form = request.form
        name = form['name']
        email = form['email']
        phone = form['phone']
        image = request.files['image']
        image = b64encode(image.read())
        account.update(name = name, image = image, email = email, phone = phone)
        url = '/edit.profile/' + username_url
        return redirect(url)




@app.route('/friend.request/<method>/<username_url>', methods=['GET','POST'])
def friend_request_method(method, username_url):
    username = session['username']
    account = Account.objects.get(username = username)
    account_other = Account.objects.get(username = username_url)
    url = '/profile/' + username_url
    if method == "delete.friend":
        account.update(pull__friendlist = account_other.username)
        account_other.update(pull__friendlist = account.username)
        return redirect(url)
    elif method == "cancel":
        account.update(pull__friend_request_sent = account_other.username)
        account_other.update(pull__friend_accept_pending = account.username)
        return redirect(url)
    elif method == "accept":
        account.update(add_to_set__friendlist = account_other.username)
        account.update(pull__friend_accept_pending = account_other.username)
        account_other.update(add_to_set__friendlist = account.username)
        account_other.update(pull__friend_request_sent = account.username)
        return redirect(url)
    elif method == "send.request":
        account.update(add_to_set__friend_request_sent = account_other.username)
        account_other.update(add_to_set__friend_accept_pending = account.username)
        return redirect(url)
    elif method == "decline":
        account.update(pull__friend_accept_pending = account_other.username)
        account_other.update(pull__friend_request_sent = account.username)
        return redirect(url)



    # friendlist = ListField()
    # friend_request_sent = ListField()
    # friend_accept_pending = ListField()




class Contract_type_1(Document):
    contract_maker = StringField()
    contract_term = StringField()
    party_left = StringField()
    party_right = StringField()
    spectator = StringField()
    punishment = StringField()
    winner = ListField()
    #claim victory
    victory_claim = StringField()



# for contract in Contract_type_1:
#     if contract.victory_claim in party_left:



@app.route('/claim.victory/<username>/<contract_id>', methods=['GET','POST'])
def claim_victory(username,contract_id):
    contract_type_1 = Contract_type_1.objects().with_id(contract_id)
    contract_type_1.update(add_to_set__victory_claim = username)
    url = '/profile/' + username
    return redirect(url)


@app.route('/contract.type.1', methods=['GET','POST'])
def contract_type_1():
    username = session['username']
    account = Account.objects.get(username = username)
    if request.method == "GET":
        return render_template('contract_type_1.html', account = account)
    elif request.method == "POST":
        form = request.form
        contract_maker = username
        contract_term = form['contract_term']
        party_left = form['party_left']
        party_right = form['party_right']
        spectator = form['spectator']
        punishment = form['punishment']
        # print(party_left)
        # return ""
        contract_type_1 = Contract_type_1(  contract_maker = contract_maker,
                                            contract_term = contract_term,
                                            party_left = party_left,
                                            party_right = party_right,
                                            spectator = spectator,
                                            punishment = punishment)
        contract_type_1.save()
        account.update(add_to_set__active_bet = str(contract_type_1.id))
        url = '/profile/' + username
        return redirect(url)
        #
        # for player in party_left and party_right:
        #     player_pending_bet = Account.objects.get(username = player)
        #     player_pending_bet.update(add_to_set__pending_bet = Contract_type_1.id)
        # account.update(add_to_set__friend_request_sent = account_other.username)
        # account_other.update(add_to_set__friend_accept_pending = account.username)


@app.route('/logout', methods = ['GET'])
def logout():
    del session['username']
    return redirect('/login')

if __name__ == '__main__':
  app.run(debug=True)
