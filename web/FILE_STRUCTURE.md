# Dora Web Application - File Structure & Implementation

## Complete File Tree

```
/home/user/Dora/web/
├── package.json                  # Dependencies and scripts
├── tsconfig.json                 # TypeScript configuration
├── next.config.js                # Next.js configuration
├── tailwind.config.ts            # Tailwind CSS configuration
├── postcss.config.js             # PostCSS configuration
├── components.json               # shadcn/ui configuration
├── .eslintrc.json               # ESLint configuration
├── .gitignore                   # Git ignore rules
├── .env.local                   # Environment variables (local)
├── README.md                    # Project documentation
│
├── app/                         # Next.js App Router pages
│   ├── layout.tsx              # Root layout with providers
│   ├── page.tsx                # Landing page (/)
│   ├── globals.css             # Global styles
│   │
│   ├── login/
│   │   └── page.tsx           # Login page with SSO
│   │
│   ├── register/
│   │   └── page.tsx           # Registration page
│   │
│   ├── dashboard/
│   │   ├── layout.tsx         # Dashboard layout with auth
│   │   └── page.tsx           # Main dashboard
│   │
│   ├── query/
│   │   ├── layout.tsx         # Protected layout
│   │   └── page.tsx           # Medical query interface
│   │
│   ├── drugs/
│   │   ├── layout.tsx         # Protected layout
│   │   └── page.tsx           # Drug interaction checker
│   │
│   ├── history/
│   │   ├── layout.tsx         # Protected layout
│   │   └── page.tsx           # Query history
│   │
│   ├── settings/
│   │   ├── layout.tsx         # Protected layout
│   │   └── page.tsx           # User settings
│   │
│   └── pricing/
│       └── page.tsx            # Pricing & subscription
│
├── components/
│   ├── app-sidebar.tsx         # Navigation sidebar
│   ├── app-header.tsx          # Header with user menu
│   │
│   └── ui/                     # shadcn/ui components
│       ├── button.tsx          # Button component
│       ├── card.tsx            # Card component
│       ├── input.tsx           # Input component
│       ├── label.tsx           # Label component
│       └── dropdown-menu.tsx   # Dropdown menu component
│
├── lib/
│   ├── api.ts                  # API client with auth
│   ├── auth-context.tsx        # Authentication provider
│   └── utils.ts                # Utility functions (cn)
│
└── types/
    └── api.ts                  # TypeScript API types
```

## Key Components & Features

### 1. Authentication System
**Files:** `lib/api.ts`, `lib/auth-context.tsx`, `app/login/page.tsx`, `app/register/page.tsx`

- Email/password authentication
- SSO support (Google, Microsoft)
- JWT token management with auto-refresh
- Protected routes with auth context
- Session management

### 2. Medical Query Interface
**File:** `app/query/page.tsx`

- Real-time medical question answering
- AI-powered responses with citations
- Confidence scoring
- Evidence-based answers
- Voice input support (UI ready)
- Query history tracking

### 3. Drug Interaction Checker
**File:** `app/drugs/page.tsx`

- Multi-drug interaction checking
- Severity levels (Contraindicated, Major, Moderate, Minor)
- Patient medication context
- Drug normalization via RxNorm
- Management recommendations
- Visual severity indicators

### 4. Dashboard
**File:** `app/dashboard/page.tsx`

- Quick action cards
- Usage statistics
- Recent activity feed
- Subscription status banner
- Personalized greeting

### 5. User Settings
**File:** `app/settings/page.tsx`

- Profile management
- Notification preferences
- Security settings (2FA, password)
- Active session management
- Account deletion

### 6. Pricing & Subscriptions
**File:** `app/pricing/page.tsx`

- Three-tier pricing (Free, Professional, Institution)
- Monthly/Annual billing toggle
- Feature comparison
- FAQ section
- Payment integration ready

## API Integration

### Authentication Endpoints
```typescript
POST /api/v1/auth/register      // User registration
POST /api/v1/auth/login         // Email/password login
POST /api/v1/auth/refresh       // Token refresh
POST /api/v1/auth/logout        // Logout
GET  /api/v1/auth/me            // Get current user
POST /api/v1/auth/sso/init      // Initialize SSO
POST /api/v1/auth/sso/callback  // SSO callback
```

### Query Endpoints
```typescript
POST /api/v1/query              // Medical query
GET  /api/v1/stats              // Knowledge base stats
```

### Drug Endpoints
```typescript
POST /api/v1/drugs/check        // Check interactions
GET  /api/v1/drugs/normalize/{name}  // Normalize drug name
```

### License Endpoints
```typescript
GET  /api/v1/license/status     // License status
POST /api/v1/license/activate   // Activate license
```

## TypeScript Types

### User & Authentication
```typescript
interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  specialty?: string;
  institution?: string;
  license_tier: string;
  // ... more fields
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}
```

### Medical Query
```typescript
interface MedicalQuery {
  question: string;
  patient_id?: number;
  patient_context?: PatientContext;
  top_k?: number;
}

interface MedicalAnswer {
  answer: string;
  citations: Citation[];
  confidence_score: number;
  retrieved_chunks: number;
  query_time_ms: number;
  warnings: string[];
}
```

### Drug Interactions
```typescript
interface DrugInteraction {
  drug1: string;
  drug2: string;
  severity: "minor" | "moderate" | "major" | "contraindicated";
  description: string;
  management: string;
  source: string;
}
```

## Styling & Design

### Theme Colors
- **Primary:** #0066CC (Medical Blue)
- **Primary Variants:** 50-900 scale
- **Dark Mode:** Full support

### Responsive Breakpoints
- **Mobile:** < 768px
- **Tablet:** 768px - 1024px
- **Desktop:** > 1024px

### Key Design Principles
1. Clean, Apple-like aesthetic
2. Medical blue primary color
3. High contrast for readability
4. Consistent spacing (Tailwind)
5. Accessible components (Radix UI)
6. Dark mode throughout

## State Management

### Auth Context
```typescript
const { user, isLoading, isAuthenticated, login, logout } = useAuth();
```

### React Query (Ready for use)
```typescript
const { data, isLoading, error } = useQuery(['key'], fetchFunction);
```

## Next Steps for Production

1. **Add Error Boundaries**
   - Wrap pages in error boundaries
   - Custom error pages (404, 500)

2. **Implement Analytics**
   - Google Analytics / Plausible
   - User behavior tracking

3. **Optimize Performance**
   - Image optimization
   - Code splitting
   - Lazy loading

4. **Add Tests**
   - Unit tests (Jest)
   - Integration tests (Cypress)
   - E2E tests

5. **SEO Optimization**
   - Meta tags for all pages
   - Sitemap generation
   - Open Graph tags

6. **Security Enhancements**
   - Rate limiting
   - CSRF protection
   - Input validation

7. **Accessibility**
   - ARIA labels
   - Keyboard navigation
   - Screen reader support

## Environment Variables

### Required for Production
```env
NEXT_PUBLIC_API_URL=https://api.dora.docassist.com
NEXT_PUBLIC_APP_NAME=Dora
NEXT_PUBLIC_APP_VERSION=0.1.0
```

### Optional
```env
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_SENTRY_DSN=https://...
```

## Build & Deploy

### Local Development
```bash
npm install
npm run dev
```

### Production Build
```bash
npm run build
npm run start
```

### Docker Deployment (Future)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Performance Considerations

1. **Route Pre-fetching:** Next.js automatically pre-fetches linked pages
2. **Image Optimization:** Use Next.js Image component
3. **API Caching:** React Query handles caching automatically
4. **Code Splitting:** App Router splits code by route
5. **Static Generation:** Consider ISR for marketing pages

## Accessibility Features

- Semantic HTML throughout
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus management in modals
- Color contrast ratios meet WCAG 2.1 AA
- Screen reader friendly

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari
- Chrome Mobile

## Notes for Developers

1. **All API calls** go through the centralized `apiClient`
2. **Authentication** is handled by the `AuthProvider` context
3. **Protected routes** use the dashboard layout which checks auth
4. **Styling** follows Tailwind utility-first approach
5. **Components** are built with shadcn/ui for consistency
6. **Types** are defined in `types/api.ts` for API responses
7. **Dark mode** is supported via Tailwind's dark: prefix

## Contact

For questions or issues, contact the DocAssist development team.

---

**Last Updated:** January 2026
**Version:** 0.1.0
**Status:** Ready for development/testing
