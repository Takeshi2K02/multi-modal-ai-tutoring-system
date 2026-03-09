import React, { useEffect, useRef, useState } from 'react';
import { API_BASE_URL } from '../services/api';

const LiveAffectSensing = ({ userId = "alex_123", materialId = "active_lesson", enabled = false, interactionId = null }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [cameraActive, setCameraActive] = useState(false);
    const streamRef = useRef(null);

    useEffect(() => {
        if (!enabled) {
            console.log(">>> [CV] Camera disabled by prop. Cleaning up.");
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop());
                streamRef.current = null;
            }
            setCameraActive(false);
            return;
        }

        const startCamera = async () => {
            try {
                // Request stream
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 320, height: 240 }
                });
                streamRef.current = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    setCameraActive(true);
                    console.log(">>> [CV] Camera Activated Globally");
                }
            } catch (err) {
                console.error(">>> [CV] Camera Access Denied:", err);
            }
        };

        startCamera();

        const captureInterval = setInterval(() => {
            if (videoRef.current && canvasRef.current && cameraActive && enabled) {
                const canvas = canvasRef.current;
                const video = videoRef.current;

                // Ensure video is ready
                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    const context = canvas.getContext('2d');
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const frame = canvas.toDataURL('image/jpeg', 0.5);

                    fetch(`${API_BASE_URL}/api/engagement/track`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            frame: frame.split(',')[1],
                            user_id: userId,
                            material_id: materialId,
                            interaction_id: interactionId
                        })
                    }).catch(e => console.warn(">>> [CV] Backend Offline"));
                }
            }
        }, 2000); // 2s interval for background monitoring

        return () => {
            console.log(">>> [CV] Cleaning up global camera stream");
            clearInterval(captureInterval);
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop());
                streamRef.current = null;
            }
        };
    }, [userId, materialId, cameraActive, enabled]);

    return (
        <div className="fixed bottom-4 right-4 z-[9999] pointer-events-none opacity-0 overflow-hidden w-1 h-1">
            <video ref={videoRef} autoPlay playsInline muted width="320" height="240" />
            <canvas ref={canvasRef} width="320" height="240" />
        </div>
    );
};

export default LiveAffectSensing;
