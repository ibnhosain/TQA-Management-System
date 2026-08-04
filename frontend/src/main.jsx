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

// Android/Windows/Mac-এ Chrome/Edge নিজে থেকেই "ইনস্টল করবেন?" পপআপ দেখানোর
// ক্ষমতা রাখে (beforeinstallprompt) — ব্রাউজার ডিফল্টে সেটা চেপে রাখে, আমরা
// ধরে রাখি (window.__tqaInstallEvent) যাতে পরে নিজেদের বাটনে ক্লিকে দেখাতে পারি
// (তখনই আসল এক-ক্লিক "Install" পপআপ আসবে)। iOS Safari এই ইভেন্ট কখনো দেয় না
// (Apple-এর সীমাবদ্ধতা) — সেখানে ম্যানুয়াল "Add to Home Screen" নির্দেশনাই একমাত্র উপায়।
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  window.__tqaInstallEvent = e
  window.dispatchEvent(new Event('tqa-install-ready'))
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
