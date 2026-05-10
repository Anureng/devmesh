import { useState } from "react"
import VideoStream from "./components/VideoStream"
import ROITable from "./components/ROITable"

function App() {
  const [sessionId] = useState(() => crypto.randomUUID())

  return (
    <div style={{ display: "flex", gap: "20px", padding: "20px", fontFamily: "monospace" }}>
      <div>
        <h2>Live Feed</h2>
        <VideoStream sessionId={sessionId} />
      </div>
      <div style={{ flex: 1 }}>
        <h2>ROI Data</h2>
        <ROITable sessionId={sessionId} />
      </div>
    </div>
  )
}

export default App