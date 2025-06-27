# Canteen Management System

Modern, full-stack Canteen and Food Delivery Management System built with Django, Channels, and Firebase. This platform facilitates seamless food ordering, menu management for restaurants, and real-time order tracking for delivery personnel.

![Django](https://img.shields.io/badge/django-%23092e20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-yellow.svg?style=for-the-badge)

## Project Showcase

<div align="center">
  <table width="100%">
    <tr>
      <td width="50%"><img src="samples/Screenshot 2026-04-03 at 4.53.25 PM.png" alt="Dashboard View"></td>
      <td width="50%"><img src="samples/Screenshot 2026-04-03 at 4.54.18 PM.png" alt="Menu View"></td>
    </tr>
    <tr>
      <td width="50%"><img src="samples/Screenshot 2026-04-03 at 4.54.32 PM.png" alt="Order Tracking"></td>
      <td width="50%"><img src="samples/Screenshot 2026-04-03 at 4.54.40 PM.png" alt="Mobile Experience"></td>
    </tr>
  </table>
</div>

## Key Features

### Role-Based Access Control
- **Customers**: Browse menus (categorized by submenus), add items to carts with price snapshots, and track orders in real-time.
- **Restaurants**: Manage dynamic menu availability, item levels, and receive instant push notifications for new orders.
- **Delivery Personnel**: Dedicated workflow for accepting and completing deliveries with secure PIN verification.
- **Administrators**: Full system oversight, notification management, and dynamic pricing configuration.

### Intelligent Ordering System
- **Real-Time Updates**: Live order status via Django Channels (WebSockets) and Redis.
- **Secure Verification**: Orders are fulfilled using a secure 4-digit PIN system.
- **Automated Billing**: Dynamic calculation of GST, packaging, delivery, and platform fees based on order type (Delivery, Pickup, Dining).
- **Stock Management**: Real-time inventory tracking with automatic item unavailability upon stock depletion.

### Robust Infrastructure
- **Payment Integration**: Secure transaction handling with support for UPI, Cards, and NetBanking (PayU and PhonePe).
- **Cloud Notifications**: Firebase Cloud Messaging (FCM) integration for cross-platform push notifications.
- **Verified Communication**: Email verification system using secure UUID-based request tracking.

## Tech Stack

- **Backend**: Django 5.1 & Django REST Framework (DRF)
- **Real-Time**: Django Channels (WebSockets) & Redis
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Notifications**: Firebase Admin SDK (FCM)
- **Security**: Django-allauth with Social Authentication (Google)
- **Asset Management**: Whitenoise for efficient static file serving
- **Environment**: Decoupled configuration via `.env` files

## Installation & Setup

### Prerequisites
- Python 3.10+
- Redis (required for WebSocket support)
- PostgreSQL (optional, can be configured in `.env`)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/canteen.git
   cd canteen
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file from the provided template:
   ```bash
   cp .env.example .env
   ```
   Provide your specific credentials:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `GOOGLE_OAUTH_CLIENT_ID` / `SECRET`
   - `FIREBASE_SECRET_JSON`
   - `PAYU_KEY` / `SALT`

5. **Initialize Database**
   ```bash
   python manage.py migrate
   ```

6. **Running the Application**
   For local development:
   ```bash
   python manage.py runserver
   ```
   For production-ready WebSocket support:
   ```bash
   daphne -p 8000 canteen.asgi:application
   ```

## Project Structure

```text
├── canteen/               # Main project configuration (settings, wsgi, asgi)
├── canteenapp/            # core application logic, models, views, and consumers
│   ├── consumers.py       # WebSocket/Async logic
│   ├── firebase.py        # FCM integration
│   ├── models.py          # Data schema
│   └── views.py           # Backend controllers
├── samples/               # Project screenshots and assets
├── static/                # Static assets (CSS, JS, Images)
├── staticfiles/           # Collected static files for production
├── manage.py              # Django management script
└── requirements.txt       # Project dependencies
```

## Contributing

Professional contributions are welcome. Please adhere to the established [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Developed by [Harshavardhan Vemali](https://github.com/HarshavardhanVemali)
