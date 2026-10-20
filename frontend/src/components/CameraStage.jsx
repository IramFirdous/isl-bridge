
import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";

import {
  drawHands,
  loadHandLandmarker,
  serializeHands,
} from "../hands";

const CameraStage = forwardRef(function CameraStage(
  { enabled, statusText },
  ref
) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const bufferRef = useRef([]);

  const [error, setError] = useState("");

  useImperativeHandle(ref, () => ({
    frames: () => bufferRef.current.slice(),
    framesCount: () => bufferRef.current.length,
    clear: () => {
      bufferRef.current = [];
    },
  }));

  useEffect(() => {
    if (!enabled) {
      bufferRef.current = [];
      return undefined;
    }

    let stream = null;
    let raf = 0;
    let cancelled = false;
    let activeVideo = null;

    setError("");
    bufferRef.current = [];

    async function startCamera() {
      try {
        // Load the MediaPipe model.
        const landmarker = await loadHandLandmarker();

        // The component might have been closed while loading.
        if (cancelled) return;

        if (!navigator.mediaDevices?.getUserMedia) {
          throw new Error(
            "Camera access is unavailable. Use localhost or HTTPS."
          );
        }

        // Request camera access.
        const newStream =
          await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: "user",
              width: 640,
              height: 480,
            },
            audio: false,
          });

        // If cleanup happened while the permission request was pending,
        // immediately stop the stream instead of attaching it.
        if (cancelled) {
          newStream.getTracks().forEach((track) => track.stop());
          return;
        }

        stream = newStream;

        const video = videoRef.current;

        if (!video) {
          stream.getTracks().forEach((track) => track.stop());
          stream = null;
          return;
        }

        activeVideo = video;
        video.srcObject = stream;

        await video.play();

        // Do not start processing after cleanup.
        if (cancelled) return;

        function loop() {
          if (cancelled) return;

          if (
            video.readyState >= 2 &&
            video.videoWidth > 0 &&
            video.videoHeight > 0
          ) {
            const result = landmarker.detectForVideo(
              video,
              performance.now()
            );

            if (canvasRef.current) {
              drawHands(canvasRef.current, video, result);
            }

            bufferRef.current.push(serializeHands(result));

            if (bufferRef.current.length > 90) {
              bufferRef.current.shift();
            }
          }

          if (!cancelled) {
            raf = requestAnimationFrame(loop);
          }
        }

        loop();
      } catch (err) {
        if (!cancelled) {
          setError(
            err.message || "Unable to initialize the camera."
          );
        }
      }
    }

    startCamera();

    return () => {
      cancelled = true;

      cancelAnimationFrame(raf);

      if (activeVideo) {
        activeVideo.pause();
        activeVideo.srcObject = null;
      }

      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }

      bufferRef.current = [];
    };
  }, [enabled]);

  return (
    <div className="stage">
      <video ref={videoRef} playsInline muted />
      <canvas ref={canvasRef} />

      {!enabled && (
        <div className="lock">
          <div>
            <strong>Camera blocked</strong>
            <p>
              Grant filming consent first. Indian Sign Language
              recognition never starts without it.
            </p>
          </div>
        </div>
      )}

      {enabled && statusText && (
        <div
          className="lock"
          style={{
            background: "transparent",
            alignItems: "end",
            justifyItems: "start",
          }}
        >
          <span className="badge">{statusText}</span>
        </div>
      )}

      {error && (
        <div className="lock">
          <div className="banner alert">{error}</div>
        </div>
      )}
    </div>
  );
});

export default CameraStage;
