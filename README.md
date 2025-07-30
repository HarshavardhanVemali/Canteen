# Canteen Management System

A robust, real-time Canteen and Food Delivery Management System built with Django, Channels, and Firebase. This platform provides a seamless experience for users to order food, for restaurants to manage their menus, and for delivery personnel to track their assignments.

## 🚀 Key Features

- **Multi-Role Support**: Tailored experiences for Customers, Delivery Personnel, Restaurants, and Administrators.
- **Real-Time Order Tracking**: Live updates on order status using Django Channels (WebSockets).
- **Comprehensive Menu Management**: Dynamic categorization with submenus and item-level availability tracking.
- **Secure Payments**: Integrated support for UPI, Cards, and NetBanking via PayU and PhonePe.
- **Push Notifications**: Firebase Cloud Messaging (FCM) integration for instant mobile alerts.
- **Automated Billing**: Dynamic calculation of GST, packaging, delivery, and platform fees.
- **Order Security**: Secure order verification using 4-digit PINs.

## 🛠 Tech Stack

- **Backend**: Django & Django REST Framework (DRF)
- **Real-Time**: Django Channels (WebSockets) & Redis
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Notifications**: Firebase Admin SDK (FCM)
- **Static Files**: Whitenoise
- **Authentication**: Django-allauth (Google Social Auth included)

## 📦 Installation & Setup

### Prerequisites
- Python 3.10+
- Redis (for Channels)
- PostgreSQL (optional)

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/canteen.git
   cd canteen
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file from the provided template:
   ```bash
   cp .env.example .env
   ```
   Fill in your secrets:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `GOOGLE_OAUTH_CLIENT_ID` / `SECRET`
   - `FIREBASE_SECRET_JSON`
   - `PAYU_KEY` / `SALT`

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Start Daphne (for WebSockets)**:
   ```bash
   daphne -p 8000 canteen.asgi:application
   ```

## 🤝 Contributing

Contributions are welcome! Please read the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before participating in this project.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Developed with ❤️ by [Harshavardhan Vemali](https://github.com/HarshavardhanVemali)
