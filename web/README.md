# Dora Web - Medical Knowledge Platform

Next.js 14 web application for Dora, the medical knowledge platform by DocAssist.

## Features

- Modern, responsive UI with Tailwind CSS and shadcn/ui
- Full authentication system (email/password + SSO)
- Medical query interface with AI-powered answers
- Drug interaction checker
- Query history tracking
- User settings and subscription management
- Dark mode support

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui (Radix UI)
- **State Management:** React Query
- **API Client:** Axios
- **Icons:** Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running at http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Dora
NEXT_PUBLIC_APP_VERSION=0.1.0
```

## Project Structure

```
web/
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Dashboard page
│   ├── query/            # Medical query interface
│   ├── drugs/            # Drug interaction checker
│   ├── history/          # Query history
│   ├── settings/         # User settings
│   ├── pricing/          # Pricing plans
│   ├── login/            # Login page
│   ├── register/         # Registration page
│   ├── layout.tsx        # Root layout
│   ├── page.tsx          # Landing page
│   └── globals.css       # Global styles
├── components/
│   ├── ui/               # shadcn/ui components
│   ├── app-sidebar.tsx   # Application sidebar
│   └── app-header.tsx    # Application header
├── lib/
│   ├── api.ts            # API client
│   ├── auth-context.tsx  # Authentication context
│   └── utils.ts          # Utility functions
├── types/
│   └── api.ts            # TypeScript type definitions
└── public/               # Static assets
```

## Key Pages

### Public Pages
- `/` - Landing page with marketing content
- `/login` - User login with SSO options
- `/register` - User registration
- `/pricing` - Pricing plans and subscription options

### Protected Pages (Require Authentication)
- `/dashboard` - Main dashboard with quick actions and stats
- `/query` - Medical query interface with AI-powered answers
- `/drugs` - Drug interaction checker
- `/history` - Query history and activity log
- `/settings` - User profile and account settings

## API Integration

The application connects to the FastAPI backend at `/api/v1/`:

- **Auth:** `/api/v1/auth/*` - Login, register, SSO, profile management
- **Query:** `/api/v1/query` - Medical question answering
- **Drugs:** `/api/v1/drugs/*` - Drug interaction checking
- **License:** `/api/v1/license/*` - Subscription management
- **Payments:** `/api/v1/payments/*` - Payment processing

## Development

### Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

### Adding New Components

The project uses shadcn/ui components. To add a new component:

```bash
npx shadcn-ui@latest add [component-name]
```

## Design System

### Colors

- **Primary:** Medical Blue (#0066CC)
- **Gradients:** Primary-50 to Primary-900
- **Dark Mode:** Full support with automatic theme switching

### Typography

- **Font:** Inter (from Google Fonts)
- **Sizes:** Responsive, mobile-first approach

### Components

All UI components follow the shadcn/ui design system:
- Buttons, Cards, Inputs, Labels
- Dropdown menus, Dialogs, Tabs
- Custom components for medical-specific features

## Authentication Flow

1. User registers or logs in (email/password or SSO)
2. JWT tokens stored in localStorage
3. Auto-refresh on token expiry
4. Protected routes redirect to login if not authenticated
5. User context available via `useAuth()` hook

## Deployment

### Production Build

```bash
npm run build
npm run start
```

### Environment Setup

Ensure the following environment variables are set in production:

- `NEXT_PUBLIC_API_URL` - Backend API URL
- Any SSO credentials (handled by backend)

## Contributing

1. Follow the existing code structure
2. Use TypeScript for all new code
3. Add proper error handling
4. Test on both desktop and mobile viewports
5. Ensure dark mode compatibility

## License

Proprietary - DocAssist © 2026

## Support

For issues or questions, contact the DocAssist development team.
