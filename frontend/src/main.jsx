import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

// সার্ভিস ওয়ার্কার — PWA ইনস্টলযোগ্য করতে (Add to Home Screen/ডেস্কটপে ইনস্টল)
// এটা কোনো পারমিশন চায় না, শুধু রেজিস্টার করে রাখে; নোটিফিকেশনের অনুমতি আলাদাভাবে
// ব্যবহারকারীর ক্লিকে (enablePushNotifications) চাওয়া হয়
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
