# StoneMarket

StoneMarket is an eCommerce website built using Python's Flask framework. The website allows users to browse products, add items to their cart, proceed to checkout, and receive order confirmation emails. Admin users can manage categories and products.

## Live Version

A live version of Boredom Buster is available at the following link: [https://stonemarket.onrender.com](https://stonemarket.onrender.com).

## Features

- User Authentication (Registration, Login, Logout)
- Product Management (Admin Only)
- Category Management (Admin Only)
- Shopping Cart
- Order History and Order Details
- Stripe Payment Integration
- Email Notifications for Order Confirmations
- SMS Notifications (Optional)

## Requirements

- Python 3.7+
- Flask
- SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- Stripe
- Twilio
- Dotenv
- SMTP Server for Email Notifications

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/BAXTOR95/StoneMarket.git
   cd StoneMarket
   ```

2. **Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file at the root of the project folder with the following contents:**

   ```plaintext
   SECRET_KEY=your_secret_key
   DATABASE_URL=sqlite:///app.db
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_PUBLIC_KEY=your_stripe_public_key
   PROD=False
   ADMIN_EMAIL=admin@example.com
   MY_EMAIL=your_email@example.com
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   MY_PHONE_NUMBER=your_phone_number
   MAIL_APP_PASS=your_email_app_password
   ```

5. **Initialize the database:**

   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application:**

   ```bash
   flask run
   ```

## Project Structure

```plaintext
StoneMarket/
├── app.py
├── models.py
├── routes.py
├── forms.py
├── notification_manager.py
├── decorators.py
├── config.py
├── templates/
│   ├── add_item.html
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── cart.html
│   ├── checkout.html
│   ├── order_history.html
│   ├── order_confirmation.html
│   ├── order_details.html
│   ├── manage_categories.html
│   ├── product_details.html
│   └── email/
│       └── order_confirmation.html
├── migrations/
│   └── ...
├── instance/
│   └── ...
├── .env
├── requirements.txt
└── README.md
```

## Environment Variables

The application uses a `.env` file to store sensitive information and configuration variables. Make sure to create a `.env` file at the root of your project with the following variables:

```plaintext
SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=sqlite:///app.db
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLIC_KEY=your_stripe_public_key
PROD=False
ADMIN_EMAIL=admin@example.com
MY_EMAIL=your_email@example.com
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
MY_PHONE_NUMBER=your_phone_number
MAIL_APP_PASS=your_email_app_password
```

## Usage

- **Run the Development Server:**

  ```bash
  flask run
  ```

- **Access the Application:**

  Open your web browser and navigate to `http://127.0.0.1:5000`.

- **Admin Management:**

  To create an admin user right away, use the same email as in your `ADMIN_EMAIL` env key when registering to create a user with admin functionalities.

- **Email Notifications:**

  Ensure you have set up an SMTP server and configured your `.env` file with the correct email credentials.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contributing

1. **Fork the repository**.
2. **Create a new branch**: `git checkout -b feature-branch-name`.
3. **Commit your changes**: `git commit -m 'Add some feature'`.
4. **Push to the branch**: `git push origin feature-branch-name`.
5. **Open a pull request**.
