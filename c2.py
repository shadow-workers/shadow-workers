import os
from app import create_app, db
from flask import redirect
from config import Config

# Create FLASK APP
app = create_app()

# clear URLS table at start
db.session.execute('''delete from urls''')
db.session.commit()

@app.route('/')
def todashboard():
    return redirect('/dashboard')

print()
print("SW Token")
print(Config.AGENT_TOKEN)
print()
print("Credentials for dashboard")
print("USERNAME: " + Config.USERNAME)
print("PASSOWRD: " + Config.PASSWORD)
print()
print()

try:
    # app.debug = True
    if Config.HTTPS:
        app.run(Config.HOST, Config.PORT, ssl_context=(Config.SSL_CERT, Config.SSL_KEY))
    else:
        app.run(Config.HOST, Config.PORT)

except Exception:
    print("whattsup??")
    