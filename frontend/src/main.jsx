import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

function App() {
  const [events, setEvents] = useState([])
  const [members, setMembers] = useState([])
  const [stats, setStats] = useState({})

  const load = async () => {
    const [ev, mb, st] = await Promise.all([
      fetch('/api/events?limit=25').then(r => r.json()),
      fetch('/api/members').then(r => r.json()),
      fetch('/api/stats').then(r => r.json())
    ])
    setEvents(ev.events || [])
    setMembers(mb.members || [])
    setStats(st || {})
  }

  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t)}, [])

  return <div style={{background:'#111', color:'#eee', minHeight:'100vh', padding:16, fontFamily:'sans-serif'}}>
    <h2>Smart Arrival Camera Dashboard</h2>
    <img src="/api/stream" style={{maxWidth:'100%', border:'1px solid #333'}} />
    <h3>Stats</h3><pre>{JSON.stringify(stats, null, 2)}</pre>
    <h3>Pending Arrivals</h3>
    {events.filter(e=>e.status!=='confirmed').map(e => <div key={e.id} style={{border:'1px solid #333', margin:6, padding:8}}>
      <div>#{e.id} {e.timestamp} {e.detection_type}</div>
      {e.snapshot_path && <img src={`/${e.snapshot_path}`} style={{width:240}} />}
      <button onClick={async()=>{if(!members[0])return;await fetch(`/api/events/${e.id}/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({method:'manual',member_id:members[0].id,notes:'manual confirm'})});load()}}>Confirm as first member</button>
    </div>)}
    <h3>Members</h3>
    <ul>{members.map(m => <li key={m.id}>{m.display_name} ({m.role||'member'}) <img src={`/api/members/${m.id}/qr`} width={48} /></li>)}</ul>
  </div>
}

createRoot(document.getElementById('root')).render(<App />)
