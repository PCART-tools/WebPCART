# WebPCART

## Project Overview

WebPCART is an online analysis platform for Python program API parameter compatibility issues, built based on the PCART tool. It enables visual analysis, detection, and repair of API parameter compatibility issues in Python programs through a user-friendly web interface.

PCART project address: https://github.com/PCART-tools/PCART


## Technology Stack

- **Frontend**: 
  - Vue.js 3.5.25
- **Backend**: 
  - Python 3.9+
  - Flask 3.1.2
  - Flask-CORS 5.0.0
- **Build Tools**: 
  - Vite 7.2.4
  - npm (Node.js v22.12.0+)
- **Development Tools**: 
  - Git

## Installation

### Prerequisites

- Node.js (v22.12.0+)
- Python 3.9+
- pip

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/PCART-tools/WebPCART.git
   cd WebPCART
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd ../backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

To run both frontend and backend in development mode:

```bash
# From the frontend directory
npm run dev:all
```

## Docker Deployment

### Prerequisites

- Docker (v20.10+)
- Docker Compose (v2.0+)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/PCART-tools/WebPCART.git
   cd WebPCART
   ```

2. **Build and start services with Docker Compose**
   ```bash
   docker-compose up --build
   ```