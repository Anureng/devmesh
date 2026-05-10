import { useEffect, useState } from "react"

const API_URL = "http://localhost:8000/api/roi"

export default function ROITable({ sessionId }) {
    const [rows, setRows] = useState([])
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchROI = async () => {
            try {
                const res = await fetch(`${API_URL}?session_id=${sessionId}&limit=20`)
                if (res.status === 404) { setRows([]); return }
                if (!res.ok) throw new Error(`HTTP ${res.status}`)
                const json = await res.json()
                setRows(json.data)
                setError(null)
            } catch (e) {
                setError(e.message)
            }
        }

        fetchROI()
        const interval = setInterval(fetchROI, 2000)
        return () => clearInterval(interval)
    }, [sessionId])

    if (error) return <p style={{ color: "red" }}>Error: {error}</p>
    if (!rows.length) return <p>No ROI data yet...</p>

    return (
        <table border="1" cellPadding="6" style={{ borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
                <tr>
                    <th>Frame</th>
                    <th>X</th>
                    <th>Y</th>
                    <th>Width</th>
                    <th>Height</th>
                    <th>Confidence</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
                {rows.map((r) => (
                    <tr key={r.id}>
                        <td>{r.frame_index}</td>
                        <td>{r.x}</td>
                        <td>{r.y}</td>
                        <td>{r.width}</td>
                        <td>{r.height}</td>
                        <td>{(r.confidence * 100).toFixed(1)}%</td>
                        <td>{new Date(r.captured_at).toLocaleTimeString()}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    )
}