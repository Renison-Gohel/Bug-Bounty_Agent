
def login():
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    # Vulnerability: Hardcoded credentials
    if username == "admin" and password == "supersecret123":
        print("Login successful!")
    else:
        print("Login failed.")

if __name__ == "__main__":
    login()
