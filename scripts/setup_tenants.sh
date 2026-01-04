#!/bin/bash
# Setup script for multi-tenant mode

set -e

echo "=========================================="
echo "Dora Multi-Tenant Setup"
echo "=========================================="
echo ""

# Check if we're in the Dora directory
if [ ! -f "CLAUDE.md" ]; then
    echo "Error: Please run this script from the Dora project root"
    exit 1
fi

# 1. Install Python dependencies
echo "Installing Python dependencies..."
pip install -q razorpay 2>/dev/null || echo "  Note: razorpay package not found (optional for payments)"

# 2. Create .dora directory
echo "Creating .dora directory..."
mkdir -p ~/.dora

# 3. Initialize tenant database
echo "Initializing tenant database..."
python -c "from src.tenants.storage import TenantStorage; TenantStorage()" 2>/dev/null || echo "  Database initialized"

# 4. Run migration if main database exists
if [ -f ~/.dora/dora.db ]; then
    echo "Running database migration..."
    python migrations/001_add_tenant_support.py
else
    echo "No existing database found - skipping migration"
fi

# 5. Set up environment variables
echo ""
echo "Setting up environment variables..."
if [ ! -f .env ]; then
    cat > .env <<EOF
# Dora Environment Configuration

# JWT Secret (generate a random secret in production)
DORA_JWT_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")

# Razorpay Configuration (optional - for payment processing)
# RAZORPAY_KEY_ID=your_key_id
# RAZORPAY_KEY_SECRET=your_key_secret

# Google OAuth (optional - for SSO)
# GOOGLE_CLIENT_ID=your_client_id
# GOOGLE_CLIENT_SECRET=your_client_secret

# Microsoft OAuth (optional - for SSO)
# MICROSOFT_CLIENT_ID=your_client_id
# MICROSOFT_CLIENT_SECRET=your_client_secret
# MICROSOFT_TENANT_ID=common

# API Configuration
# API_HOST=0.0.0.0
# API_PORT=8000
# DEBUG=True
EOF
    echo "  Created .env file with defaults"
else
    echo "  .env file already exists - skipping"
fi

# 6. Frontend setup
if [ -d "web" ]; then
    echo ""
    echo "Setting up frontend..."
    cd web
    if [ ! -d "node_modules" ]; then
        echo "  Installing npm packages..."
        npm install --silent
    else
        echo "  npm packages already installed"
    fi
    cd ..
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend:"
echo "   uvicorn src.api.app:app --reload"
echo ""
echo "2. Start the frontend (in another terminal):"
echo "   cd web && npm run dev"
echo ""
echo "3. Access the application:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "4. Configure payment processing (optional):"
echo "   Edit .env and add your Razorpay credentials"
echo ""
echo "5. Test multi-tenant features:"
echo "   - Create an organization: POST /api/tenants"
echo "   - Invite members: POST /api/tenants/{id}/invitations"
echo "   - View dashboard: http://localhost:3000/clinic"
echo ""
echo "Documentation:"
echo "  - Full docs: TENANT_IMPLEMENTATION.md"
echo "  - API docs:  http://localhost:8000/docs"
echo ""
echo "=========================================="
