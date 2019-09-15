#from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import string
import sqlite3 as SQL

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure connection to use SQLite database
conn = SQL.connect("finance.db", check_same_thread=False)
conn.row_factory = SQL.Row
db = conn.cursor()

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    id=session["user_id"]
    db.execute("SELECT * FROM transactions WHERE id=(?)", (id, ))
    rows = db.fetchall()
    print(rows)
    stocks = []
    id=session["user_id"]
    db.execute("SELECT cash FROM users WHERE id=(?)", (id, ))
    cash = db.fetchall()

    for i, row in enumerate(rows):
        quote = lookup(rows[i]["symbol"])
        stocks_dict = {"symbol": quote["symbol"], "stocks": quote["name"],
                       "number": rows[i]["number"], "price": usd(quote["price"]), "total": usd(rows[i]["price"] * rows[i]["number"])}
        stocks.append(stocks_dict)

    return render_template("index.html", stocks=stocks, cash=usd(cash[0]["cash"]))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Enter symbol", 400)

        elif not request.form.get("shares"):
            return apology("Enter number of shares", 400)

        else:
            quote = lookup(request.form.get("symbol"))
            if not quote:
                return apology("Invalid symbol", 400)

            if not request.form.get("shares").isdigit():
                return apology("Invalid number", 400)

            shares = request.form.get("shares")
            id=session["user_id"]
            db.execute("SELECT cash FROM users WHERE id = (?)", (id, ))
            cash = db.fetchall()
            
            id = session["user_id"]
            stocks = quote["name"]
            symbol = quote["symbol"]
            price = quote["price"]
            worth = float(quote["price"]) * float(shares)
            money_left = float(cash[0]["cash"]) - worth
            dtime = datetime.now()
            
            if float(cash[0]["cash"]) >= worth:
                db.execute("INSERT INTO transactions (id, stocks, symbol, number, price) values(?, ?, ?, ?, ?)", (id, stocks, symbol, shares, price))
                db.execute("UPDATE users SET cash=(?) WHERE id=(?)", (money_left, id))
                db.execute("INSERT INTO history (id, symbol, shares, price, transactions) values(?,?,?,?,?)",
                           (id, symbol, shares, price, dtime))
                conn.commit()
                return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    id=session["user_id"]
    db.execute("SELECT * FROM history WHERE id=(?)", (id, ))
    rows = db.fetchall()
    print(rows)
    history = []

    for i, row in enumerate(rows):
        quote = lookup(rows[i]["symbol"])
        history_dict = {"symbol": quote["symbol"], "shares": rows[i]["shares"],
                        "price": usd(rows[i]["price"]), "transactions": rows[i]["transactions"]}
        history.append(history_dict)

    print(history)
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
    
        username=request.form.get("username")
        # Query database for username
        db.execute("SELECT * FROM users WHERE username = ?", (username, ))
        rows = db.fetchall()
        print(rows)
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        else:
            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Enter symbol", 400)

        else:
            quote = lookup(request.form.get("symbol"))
            if not quote:
                return apology("Invalid symbol", 400)

            return render_template("quoted.html", name=quote["name"], price=usd(quote["price"]), symbol=quote["symbol"])
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not (request.form.get("password") or len(request.form.get("password")) < 6):
            return apology("must provide password", 400)

        elif not request.form.get("confirmation"):
            return apology("must provide password", 400)

        elif not (request.form.get("password") == request.form.get("confirmation") or len(request.form.get("password")) < 6):
            return apology("passwords don't match!", 400)

        else:
            password = request.form.get("password")
            special = set(string.punctuation.replace("_", ""))
            if any(char in special for char in password):
                passhash = generate_password_hash(request.form.get("password"))
                username = request.form.get("username")
                db.execute("INSERT INTO users (username,hash) VALUES(?, ?)",(username, passhash))
                conn.commit()
                db.execute("SELECT * FROM users WHERE username = (?)", (username, ))
                result = db.fetchall()
                print(result)
                if not result:
                    return apology("Username already exists", 400)
                else:
                    username=request.form.get("username")
                    print(username)
                    # Query database for username
                    db.execute("SELECT * FROM users WHERE username = (?)", (username, ))
                    rows = db.fetchall()
                    # rows = dict(rows)
                    print(rows)
                    session["user_id"] = rows[0][0]
                    return redirect("/login")
            else:
                return apology("Must contain special characters", 400)
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
     # Ensure username was submitted
        if not request.form.get("symbol"):
            return apology("must select symbol", 400)

        # Ensure password was submitted
        elif not request.form.get("shares"):
            return apology("must enter number", 400)

        elif not request.form.get("shares").isdigit():
            return apology("Invalid number", 400)
    
        id=session["user_id"]
        symbol=request.form.get("symbol")
        
        db.execute("SELECT number FROM transactions WHERE id = (?) AND symbol=(?)",
                   (id, symbol))
        number = db.fetchall()

        for it, items in enumerate(number):
            if int(request.form.get("shares")) > int(number[it]["number"]):
                return apology("You don't have enough shares", 400)

        num = request.form.get("shares")
        dtime = datetime.now()
        quote = lookup(request.form.get("symbol"))
        symbol = quote["symbol"]
        db.execute("SELECT number FROM transactions where id=(?) AND symbol=?",
                   (id, symbol))
        shares = db.fetchall()
        shares_left = int(shares[0]["number"]) - int(num)
        price=quote["price"]

        db.execute("UPDATE transactions SET number=? where id=? AND symbol=?",
                   (shares_left, id, symbol))
        cash_left = shares_left * quote["price"]
        db.execute("UPDATE users SET cash=? where id=?", (cash_left, id))
        db.execute("INSERT INTO history (symbol, shares, price, transactions) values(?, ?, ?, ?)",
                   (symbol, num, price, dtime))
        conn.commit()
        return redirect("/")

    else:
        id=session["user_id"]
        db.execute("SELECT symbol FROM transactions WHERE id = ?", (id, ))
        symbols = db.fetchall()
        return render_template("sell.html", symbols=symbols)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
