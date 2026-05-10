import { useEffect, useRef, useState } from "react"

const WS_URL = "ws://localhost:8000/ws/stream"

export default function VideoStream({ sessionId }) {
    const videoRef = useRef(null)
    const canvasRef = useRef(null)
    const wsRef = useRef(null)
    const [annotatedSrc, setAnnotatedSrc] = useState(null)
    const [status, setStatus] = useState("Connecting...")
    const prevUrlRef = useRef(null)

    useEffect(() => {
        // 1. Open WebSocket, send session_id first
        const ws = new WebSocket(WS_URL)
        ws.binaryType = "blob"
        wsRef.current = ws

        ws.onopen = () => {
            ws.send(sessionId)
            setStatus("Connected")
        }

        ws.onclose = () => setStatus("Disconnected")
        ws.onerror = () => setStatus("Error")

        // 2. Receive annotated frame back, display it
        ws.onmessage = (event) => {
            const url = URL.createObjectURL(event.data)
            setAnnotatedSrc((prev) => {
                if (prevUrlRef.current) URL.revokeObjectURL(prevUrlRef.current)
                prevUrlRef.current = url
                return url
            })
        }

        return () => ws.close()
    }, [sessionId])

    useEffect(() => {
        // 3. Access webcam
        navigator.mediaDevices.getUserMedia({ video: true })
            .then((stream) => {
                if (videoRef.current) {
                    videoRef.current.srcObject = stream
                    videoRef.current.play().catch(e => console.error("Video play failed:", e))
                }
            })
            .catch(e => {
                console.error("Webcam access error:", e)
                setStatus("Webcam Error")
            })
    }, [])

    useEffect(() => {
        // 4. Capture frames from webcam at ~15fps, send to WebSocket
        const canvas = canvasRef.current
        const video = videoRef.current
        if (!canvas || !video) return

        const interval = setInterval(() => {
            if (wsRef.current?.readyState !== WebSocket.OPEN) return
            const ctx = canvas.getContext("2d")
            canvas.width = video.videoWidth || 640
            canvas.height = video.videoHeight || 480
            ctx.drawImage(video, 0, 0)
            canvas.toBlob(
                (blob) => { if (blob) wsRef.current.send(blob) },
                "image/jpeg",
                0.8
            )
        }, 66) // ~15fps

        return () => clearInterval(interval)
    }, [])

    return (
        <div>
            <p>Status: {status}</p>
            {/* Hidden: captures webcam frames */}
            {/* Video element must be "visible" to the browser to play and provide frames, but we hide it from the user */}
            <video 
                ref={videoRef} 
                autoPlay 
                muted 
                playsInline
                style={{ 
                    position: "absolute", 
                    width: "1px", 
                    height: "1px", 
                    opacity: 0, 
                    pointerEvents: "none" 
                }} 
            />
            <canvas ref={canvasRef} style={{ display: "none" }} />
            {/* Shown: annotated feed from server */}
            {annotatedSrc
                ? <img src={annotatedSrc} alt="Annotated feed" style={{ width: 640, border: "2px solid #0f0" }} />
                : <div style={{ width: 640, height: 480, background: "#111", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center" }}>Waiting for feed...</div>
            }
        </div>
    )
}