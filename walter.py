from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import numpy as np
import pickle
import sklearn

print(sklearn.__version__)
#loading models
dtr = pickle.load(open('dtr.pkl','rb'))
preprocessor = pickle.load(open('preprocessor.pkl','rb'))

app = Flask(__name__)
app.secret_key = 'fzytpxvLe48W0r56A_Leng'

DB_HOST = "localhost"
DB_NAME = "sampledb"
DB_USER = "postgres"
DB_PASS = "37887635"

def connect_db():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

@app.route('/')
def index():
    return render_template('home.html')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = connect_db()
        cur = conn.cursor()
        
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if the username and email are unique
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_email = cur.fetchone()

        if existing_user:
            flash('Username already exists!', 'error')
        elif existing_email:
            flash('Email already exists!', 'error')
        elif password != confirm_password:
            flash('Passwords do not match!', 'error')
        else:
            cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
            conn.commit()
            flash('Registration successful!', 'success')

        cur.close()
        conn.close()
        return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = connect_db()
        cur = conn.cursor()
        
        email = request.form['email']
        password = request.form['password']

        cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user[0]  # Storing user ID in the session
            flash('Login successful!', 'success')
        else:
            flash('Invalid email or password!', 'error')

        cur.close()
        conn.close()
        return redirect(url_for('home'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.pop('user_id', None)  # Clear user ID from session
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    else:
        return render_template('logout.html')  # Render a template for confirmation
    
@app.route("/cow")
def cow():
      # Example data to pass to the template
    return render_template("cow.html")


@app.route('/cow', methods=['POST'])
def add_cow():
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to add a cow.', 'error')
            return redirect(url_for('login'))
        
        conn = connect_db()
        cur = conn.cursor()
        
        litres_of_water = request.form['Litres_of_water_Taken_by_the_cow_in_a_day']
        no_of_calves = request.form['No_of_Calves']
        yearly_yield = request.form['Yearly_yield']
        cow_breed = request.form['Cow_Breed']
        user_id = session['user_id']  # Get user ID from session
        
        cur.execute("INSERT INTO cow (litres_of_water, no_of_calves, yearly_yield, cow_breed, user_id) VALUES (%s, %s, %s, %s, %s)", (litres_of_water, no_of_calves, yearly_yield, cow_breed, user_id))
        conn.commit()
        flash('Cow data added successfully!', 'success')

        cur.close()
        conn.close()
        return redirect(url_for('home'))
    
@app.route("/view_cows")
def view_cows():
    if 'user_id' not in session:
        flash('Please log in to view your cows.', 'error')
        return redirect(url_for('login'))
    
    conn = connect_db()
    cur = conn.cursor()

    user_id = session['user_id']  # Get user ID from session
    cur.execute("SELECT * FROM cow WHERE user_id = %s", (user_id,))
    cows = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("view_cows.html", cows=cows)

@app.route("/predict")
def pred():
      # Example data to pass to the template
    return render_template("hello.html")

@app.route("/predict",methods=['POST'])
def predict():
    if request.method == 'POST':
        Average_Temperature_of_the_Area = request.form['Average_Temperature_of_the_Area']
        Litres_of_water_Taken_by_the_cow_in_a_day = request.form['Litres_of_water_Taken_by_the_cow_in_a_day']
        No_of_Calves = request.form['No_of_Calves']
        Cow_Breed = request.form['Cow_Breed']
        Feeding_Practices = request.form['Feeding_Practices']
        Area = request.form['Area']
        
        features = np.array([[Average_Temperature_of_the_Area, Litres_of_water_Taken_by_the_cow_in_a_day,No_of_Calves, Cow_Breed,Feeding_Practices,Area]],dtype=object)
        transformed_features = preprocessor.transform(features)
        prediction = dtr.predict(transformed_features).reshape(1,-1)
        
        
        # Convert the prediction NumPy array to a Python scalar value
        prediction = prediction[0][0] 

        # Save prediction data in the database
        
        conn = connect_db()
        cur = conn.cursor()
        user_id = session['user_id']
        cur.execute("INSERT INTO predict (average_temperature, litres_of_water, no_of_calves, cow_breed, feeding_practices, area, prediction, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (Average_Temperature_of_the_Area, Litres_of_water_Taken_by_the_cow_in_a_day, No_of_Calves, Cow_Breed, Feeding_Practices, Area, prediction, user_id))
        conn.commit()
        cur.close()
        conn.close()

    return render_template('hello.html',prediction = prediction)

@app.route("/view_predictions")
def view_predictions():
    conn = connect_db()
    cur = conn.cursor()

    user_id = session.get('user_id')  # Get user ID from session
    cur.execute("SELECT * FROM predict WHERE user_id = %s", (user_id,))
    predictions = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("view_predictions.html", predictions=predictions)


if __name__ == '__main__':
    app.run(debug=True)
