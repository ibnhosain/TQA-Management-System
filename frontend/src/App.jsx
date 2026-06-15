import React from 'react'
import TQAManagementSystem from './tqa-management-system'

/* সাদা স্ক্রিন এড়াতে: কোনো render-error হলে পুরো অ্যাপ ভেঙে না পড়ে আসল বার্তা দেখাবে */
class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('App crash:', error, info); }
  render() {
    if (this.state.error) {
      const msg = String(this.state.error?.stack || this.state.error?.message || this.state.error)
      return (
        <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 20, fontFamily: "'Hind Siliguri', 'Noto Sans Bengali', sans-serif", background: '#f6faf7' }}>
          <div style={{ maxWidth: 580, width: '100%', background: '#fff', border: '1px solid #e5e9e5', borderRadius: 16, padding: 24, textAlign: 'center' }}>
            <div style={{ fontSize: 40 }}>🕌</div>
            <div style={{ fontWeight: 800, fontSize: 18, color: '#1a5c3a', marginTop: 8 }}>একটু সমস্যা হয়েছে</div>
            <div style={{ fontSize: 13, color: '#6b7280', marginTop: 6 }}>পেজটি লোড করতে একটি ত্রুটি হয়েছে। নিচের বার্তাটির স্ক্রিনশট নিয়ে জানালে ঠিক করে দেওয়া যাবে।</div>
            <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#f4f6f4', borderRadius: 10, padding: 12, marginTop: 14, fontSize: 11.5, color: '#c2410c', maxHeight: 220, overflow: 'auto' }}>{msg}</pre>
            <button onClick={() => { this.setState({ error: null }); window.location.reload(); }} style={{ marginTop: 16, border: 'none', background: '#1a5c3a', color: '#fff', fontWeight: 700, fontSize: 14, padding: '10px 22px', borderRadius: 10, cursor: 'pointer' }}>আবার চেষ্টা করুন</button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function App() {
  return (
    <ErrorBoundary>
      <TQAManagementSystem />
    </ErrorBoundary>
  )
}

export default App
