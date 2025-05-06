### **Step Seven: Research and Understand Login Strategy**

Look over the code in ***app.py*** related to authentication.

- How is the logged in user being kept track of?
The logged-in user is tracked using Flask's session object. When a user logs in, their user ID is stored in the session with the key CURR_USER_KEY. The session persists across requests, allowing the app to keep track of the user until they log out

```python
    session[CURR_USER_KEY] = user.id
```

- What is Flask’s ***g*** object?
Flask’s g object is a global namespace for holding data during the lifespan of a request. It's useful for storing information that needs to be accessible across different parts of the request, such as the logged-in user in this case. The g object is cleared after each request.

In this code, g.user holds the current logged-in user, allowing you to access this user in any route after the add_user_to_g() function runs:

```python
    g.user = User.query.get(session[CURR_USER_KEY])
```

- What is the purpose of ***add_user_to_g ?***
The add_user_to_g() function is a before-request function. It runs before any route handler is executed and checks whether there’s a logged-in user by looking for the CURR_USER_KEY in the session. If a user is logged in, it retrieves the user from the database and attaches it to g.user. If no user is logged in, it sets g.user to None.

This ensures that the g.user object is available in every request, so you can easily check if a user is logged in
```python
@app.before_request
def add_user_to_g():
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None
```

- What does ***@app.before_request*** mean?
The @app.before_request decorator registers a function to run before every request. This function executes before the route handlers (views) are called. It’s commonly used for tasks like checking if a user is logged in or preparing data that’s needed for many routes (e.g., adding the logged-in user to g).

In this case, add_user_to_g() runs before each request, ensuring that g.user is set up with the current user if they are logged in.