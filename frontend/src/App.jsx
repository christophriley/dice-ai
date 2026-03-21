import { useState, useRef, useEffect } from 'react'
import './App.css'

const API = 'http://localhost:5000'

function Message({ role, text }) {
  return (
    <div className={`message ${role}`}>
      <div className="bubble">{text}</div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="bubble typing">
        <span /><span /><span />
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send() {
    const text = input.trim()
    if (!text || loading) return

    setMessages(prev => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })
      const data = await res.json()

      if (!res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', text: `Error: ${data.error}` }])
      } else {
        if (!sessionId) setSessionId(data.session_id)
        setMessages(prev => [...prev, { role: 'assistant', text: data.reply }])
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Could not reach the server.' }])
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div id="chat">
      <header>
        <h1>Dice Job Search</h1>
        <p>Powered by Claude + Dice MCP</p>
      </header>

      <div className="messages">
        {messages.length === 0 && (
          <p className="empty">Describe the kind of job you&apos;re looking for.</p>
        )}
        {messages.map((m, i) => <Message key={i} {...m} />)}
        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="input-bar">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="e.g. Senior Python engineer, remote, fintech..."
          rows={1}
          disabled={loading}
        />
        <button onClick={send} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  )
}
