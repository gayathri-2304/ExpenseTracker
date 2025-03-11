import logging
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import matplotlib.pyplot as plt
import io
import base64
from waitress import serve  # Import Waitress for production server

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
# Use non-GUI backend for Matplotlib
plt.switch_backend('Agg')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.String(20), nullable=False)

# Initialize the database in the app context
def init_db():
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully.")

# Route to display the home page
@app.route('/')
def index():
    logger.info("Rendering the home page.")
    expenses = Expense.query.all()
    return render_template('home_page.html', expenses=expenses)

# Function to update or add new expense
def update_expense(category, amount, description, date):
    expense = Expense.query.filter_by(category=category).first()
    if expense:
        # Update the existing expense
        expense.amount += amount  # You can modify this logic as needed (e.g., set a new value)
        expense.description = description
        expense.date = date
        db.session.commit()
        logger.info(f"Updated expense for category {category}: {amount} on {date}.")
    else:
        # Add a new expense if the category doesn't exist
        new_expense = Expense(category=category, amount=amount, description=description, date=date)
        db.session.add(new_expense)
        db.session.commit()
        logger.info(f"Added new expense: {category} - {amount} on {date}.")

# Route to add new or update existing expense
@app.route('/add', methods=['POST'])
def add_expense():
    category = request.form['category']
    amount = float(request.form['amount'])
    description = request.form['description']
    date = request.form['date']
    update_expense(category, amount, description, date)
    return redirect(url_for('index'))

# Route to delete an expense
@app.route('/delete/<int:id>')
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    logger.info(f"Deleted expense with ID: {id}.")
    return redirect(url_for('index'))

# Route to show graph analysis
@app.route('/graph')
def graph():
    logger.info("Generating graph for expenses.")
    expenses = Expense.query.all()
    # Data preparation for the graph
    categories = [expense.category for expense in expenses]
    amounts = [expense.amount for expense in expenses]
    
    # Create a bar graph using Matplotlib
    fig, ax = plt.subplots()
    ax.bar(categories, amounts, color='skyblue')
    ax.set_xlabel('Categories')
    ax.set_ylabel('Amount')
    ax.set_title('Expenses by Category')
    plt.xticks(rotation=45, ha='right')
    
    # Save the graph to a BytesIO object to pass it to the HTML
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    
    # Encode the image to base64 to embed in HTML
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    logger.info("Graph generated successfully.")
    
    return render_template('expense_graph.html', graph_url=graph_url)

# Ensure the database is created before the first request
if __name__ == "__main__":
    logger.info("Starting the application...")
    init_db()  # Initialize the database
    logger.info("Database initialized.")
    logger.info("Server is running on http://127.0.0.1:5000")
    serve(app, host='127.0.0.1', port=5000)
