@echo off
echo Installing frontend dependencies...
cd frontend
npm install
echo Starting Next.js frontend on http://localhost:3000
npm run dev
