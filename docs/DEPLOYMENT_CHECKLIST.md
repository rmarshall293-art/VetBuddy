# VetBuddy Deployment Checklist

## Supabase
- [ ] Create project
- [ ] Run schema.sql
- [ ] Enable RLS
- [ ] Configure storage buckets
- [ ] Copy API keys to env

## Backend (FastAPI)
- [ ] Set DATABASE_URL
- [ ] Set SUPABASE_URL + KEY
- [ ] Deploy to Railway/Render
- [ ] Enable CORS

## Frontend (React)
- [ ] Set VITE_API_URL
- [ ] Set Supabase keys
- [ ] Deploy to Vercel/Netlify

## Security
- [ ] Enable RLS policies
- [ ] Use environment secrets
- [ ] Lock down public routes

## Final Validation
- [ ] Auth works
- [ ] CRUD works
- [ ] Uploads work
- [ ] AI endpoints connected
- [ ] Notifications functioning

## Optional Enhancements
- [ ] Add CI/CD (GitHub Actions)
- [ ] Add monitoring/logging
- [ ] Add analytics
