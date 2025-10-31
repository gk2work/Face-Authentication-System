# Face Authentication System - Frontend

React-based frontend application for the Face Authentication and De-duplication System.

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: Material-UI (MUI)
- **HTTP Client**: Axios with interceptors
- **Routing**: React Router v6 (to be configured)

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API client and services
│   ├── hooks/          # Custom React hooks
│   ├── types/          # TypeScript type definitions
│   ├── utils/          # Utility functions
│   ├── theme/          # MUI theme configuration
│   ├── styles/         # Global styles
│   ├── config/         # Application configuration
│   └── App.tsx         # Root component
├── public/             # Static assets
└── dist/               # Production build output
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

Build for production:

```bash
npm run build
```

The production build will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Configuration

### Environment Variables

Create a `.env.development` file for local development:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

For production, use `.env.production`:

```env
VITE_API_BASE_URL=/api
VITE_WS_BASE_URL=ws://localhost:8000
```

## Features

### API Client

The application includes a fully configured Axios client with:

- **JWT Authentication**: Automatic token injection in requests
- **Token Refresh**: Automatic token refresh on 401 errors
- **Retry Logic**: Exponential backoff for failed requests
- **Error Handling**: Centralized error handling
- **Request/Response Interceptors**: For logging and transformation

### Theme

Material-UI theme is configured with:

- Custom color palette
- Typography settings
- Component style overrides
- Responsive design support

### Path Aliases

TypeScript path aliases are configured for cleaner imports:

```typescript
import { api } from "@/services";
import { User } from "@/types";
import MyComponent from "@/components/MyComponent";
```

## API Integration

The backend API is proxied through Vite in development mode. All requests to `/api/*` are forwarded to `http://localhost:8000`.

## Next Steps

1. Implement authentication UI (login page)
2. Create dashboard with statistics
3. Build application upload interface
4. Implement identity management
5. Add WebSocket support for real-time updates
