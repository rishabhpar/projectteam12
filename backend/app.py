from flask import Flask, request, jsonify
# package to interface with mongodb
import pymongo
# passlib is the package we will use to encrypt passwords
from passlib.hash import pbkdf2_sha256
# cors is used to relax security, only for development
from flask_cors import CORS
# import class from config.py
from config import BaseConfig
# import password_strength to ensure the user's password is strong
from password_strength import PasswordPolicy
# use bcrypt to hash the email such that the same string hash the same hash
import bcrypt
# Needed to verify the server is who it says it is. Mac won't work without and Cloud stuff might not either.
import certifi
# create a Flask app
app = Flask(__name__)
CORS(app)

# connect to cloud based mongodb
client = pymongo.MongoClient("mongodb+srv://team12:adminBois&Gorls@cluster0.82uuk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority", tlsCAFile=certifi.where())
# get the specific database for user information
User_DB = client.get_database('user_information')
Account_Info = User_DB.users

Project_DB = client.get_database('project_information')
Project_Info = Project_DB.projects

# create a password policy to ensure strong passwords from users
policy = PasswordPolicy.from_names(
    length=8,  # min length: 8
    uppercase=1,  # need min. 1 uppercase letters
    numbers=1,  # need min. 1 digits
    special=1,  # need min. 1 special characters
)

# the seed for hashing a string using bcrypt
# should probably hide this
f = open("extra/salt.txt", "r")
salt = f.readline().encode()
f.close()

# route to log in to the application
# we can only POST to the API
@app.route("/api/login", methods=["POST"])
def login():  
    try:
        # extract information from the submission form
        email = request.json["email"]
        email_hashed = (bcrypt.hashpw(str.encode(email), salt)).decode()
        password = request.json["password"]

        # check for an existing user's email in the database using the way
        # the email is stored in the database
        user = Account_Info.find_one({"email": email_hashed})

        # if a user exists and the password entered in the form
        # matches, this is a successful login; else, it is an error
        # so we send back feedback
        if user and pbkdf2_sha256.verify(password, user['password']):
            return jsonify({"success": True})
        else:
            if user is None:
                # if a user with entered email does not exist, send a feedback message
                return jsonify({"error": "Entered email is not associated with a user"})
            return jsonify({"error": "Incorrect Password"})  
    except:
        return jsonify({"error": "Problem with Form"})


@app.route("/api/register", methods=["POST"])
def register():
    try:
        # pull form submission data.
        # encrypt sensitive information like email and password
        email = request.json["email"].lower()
        email_hashed = bcrypt.hashpw(str.encode(email), salt).decode()
        password = request.json["password"]
        confirm_password = request.json["confirm_password"]
        name = request.json["name"]

        # confirm the password the user chooses is strong
        if len(policy.test(password)) > 0:
            return jsonify({"error": "Password is not strong enough. Minimums: 8 characters, 1 uppercase, 1 number, 1 special"})

        # make sure the user confirms the password properly
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"})
        
        # check to see if user already exists; else, communicate with user that an
        # account already exists
        if Account_Info.find_one({"email": email_hashed}) is not None:
            return jsonify({"error": "User with that email already exists"})
        else:
            Account_Info.insert_one({"name":name, "email":email_hashed, "password":pbkdf2_sha256.hash(password)})
            
        return jsonify({"success": True})
    except:
        # there was an error while processing form submission
        return jsonify({"error": "Invalid form"})       
    

@app.route("/api/newproject", methods=["POST"])
def newproject():
    try:
        # pull form submission data.
        # encrypt sensitive information like project id
        projectID = request.json["projectid"]
        projectid_hashed = bcrypt.hashpw(str.encode(projectID), salt).decode()
        projpassword = request.json["password"]
        projectname = request.json["projName"]
        desc = request.json["description"]
        # confirm the password the user chooses is strong
        if len(policy.test(projpassword)) > 0:
            return jsonify({"error": "Password is not strong enough. Minimums: 8 characters, 1 uppercase, 1 number, 1 special"})
        
        # check to see if project already exists; else, communicate with user that this already exists
        if Project_Info.find_one({"projectid": projectid_hashed}) is not None:
            return jsonify({"error": "Project with that ID already exists"})
        else:
            Project_Info.insert_one({"projName":projectname, "projectid":projectID,"password":pbkdf2_sha256.hash(projpassword), "description":desc})
            
        return jsonify({"success": True})
    except:
        # there was an error while processing form submission
        return jsonify({"error": "Invalid form"})       

@app.route("/api/hardware", methods=["GET"])
def hardware():
    return Hardware_Info


if __name__ == "__main__":
    app.run(debug=True) # debug=True restarts the server everytime we make a change in our code