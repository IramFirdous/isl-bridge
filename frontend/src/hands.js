import { FilesetResolver, HandLandmarker } from "@mediapipe/tasks-vision";

let landmarkerPromise;

export function loadHandLandmarker() {
  if (!landmarkerPromise) {
    landmarkerPromise = (async () => {
      const fileset = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
      );
      return HandLandmarker.createFromOptions(fileset, {
        baseOptions: {
          modelAssetPath:
            "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        },
        numHands: 2,
        runningMode: "VIDEO",
        minHandDetectionConfidence: 0.5,
        minHandPresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });
    })();
  }
  return landmarkerPromise;
}

export function drawHands(canvas, video, result) {
  const ctx = canvas.getContext("2d");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!result?.landmarks) return;
  ctx.strokeStyle = "#f2c14e";
  ctx.fillStyle = "#c45c26";
  ctx.lineWidth = 3;
  const cons = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 5], [5, 6], [6, 7], [7, 8],
    [0, 9], [9, 10], [10, 11], [11, 12],
    [0, 13], [13, 14], [14, 15], [15, 16],
    [0, 17], [17, 18], [18, 19], [19, 20],
    [5, 9], [9, 13], [13, 17],
  ];
  for (const hand of result.landmarks) {
    for (const [a, b] of cons) {
      ctx.beginPath();
      ctx.moveTo(hand[a].x * canvas.width, hand[a].y * canvas.height);
      ctx.lineTo(hand[b].x * canvas.width, hand[b].y * canvas.height);
      ctx.stroke();
    }
    for (const p of hand) {
      ctx.beginPath();
      ctx.arc(p.x * canvas.width, p.y * canvas.height, 4, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

export function serializeHands(result) {
  if (!result?.landmarks?.length) return { hands: [] };
  return {
    hands: result.landmarks.map((hand) =>
      hand.map((p) => ({ x: p.x, y: p.y, z: p.z || 0 }))
    ),
  };
}
