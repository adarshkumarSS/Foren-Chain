# Forensic Case Management System (FDM-GOV)

![Django](https://img.shields.io/badge/Django-4.2.7-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-blue)
![IPFS](https://img.shields.io/badge/IPFS-Pinata_API-orange)
![License](https://img.shields.io/badge/License-MIT-blue)

A secure digital evidence management system for forensic teams with blockchain-backed file storage.

## 🔐 Core Features

### Authentication & Authorization
- **Role-based access control** (Forensic/Police/Lawyer/Court)
- Secure password policies with strength validation
- Email verification and uniqueness checks
- Session management with activity logging

### 🗂️ Case Management
- **Full CRUD operations** with audit trails
- Public/Private case classification
- Status workflow (Active → Closed → Archived)
- Multi-file evidence support per case
- Disclosure form subsystem (Police-specific)

### 🌐 IPFS Integration
- Pinata cloud service API connection
- CID-based immutable file storage
- Automatic pinning/unpinning of forensic assets
- Direct gateway access to stored evidence

### 🖥️ UI Components
- Dual navigation system (sidebar + mobile bottom bar)
- Interactive case dashboard with filtering
- Real-time notification system
- Responsive design (Desktop/Tablet/Mobile)

## 🛠️ Technical Stack

| Component          | Technology                          |
|--------------------|-------------------------------------|
| Backend Framework  | Django 4.2.7                       |
| Frontend           | Bootstrap 5.3 + jQuery 3.6         |
| Database           | PostgreSQL (default: SQLite)        |
| File Storage       | Pinata IPFS + Local cache           |
| Authentication     | Django Allauth                      |
| Form Handling      | Django Crispy Forms (bootstrap4)    |
| Security           | CSRF, CORS, Rate Limiting           |

## ✨ Key Improvements

- Fixed template inheritance issues
- Resolved jQuery conflicts with modern ES6
- Implemented mobile-first responsive design
- Added client-side form validation
- Enhanced visual feedback systems
- Optimized IPFS file handling

## 🚀 Future Roadmap

| Priority | Feature                          | Status  |
|----------|----------------------------------|---------|
| High     | Evidence chain-of-custody        | Planned |
| High     | Multi-factor authentication      | Planned |
| Medium   | Case timeline visualization      | Backlog |
| Medium   | Bulk evidence uploads            | Backlog |
| Low      | Advanced search filters          | Idea    |

## 🧰 Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/fdm-gov.git
cd fdm-gov

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
