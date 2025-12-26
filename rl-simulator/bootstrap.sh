#!/usr/bin/env bash
set -e

# 1. Backend
mkdir -p backend
cat > backend/requirements.txt << 'EOF'
fastapi
uvicorn
pydantic
numpy
EOF

cat > backend/main.py << 'EOF'
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vocab = ['A','B','C','D']
theta = np.zeros(len(vocab))

class RLSimRequest(BaseModel):
    reward_weight: float
    learning_rate: float
    episodes: int

@app.post("/api/rl/simulate")
def simulate(req: RLSimRequest):
    global theta
    theta = np.zeros(len(vocab))
    rewards = []
    for _ in range(req.episodes):
        probs = np.exp(theta) / np.exp(theta).sum()
        action = np.random.choice(len(vocab), p=probs)
        r = 1.0 if action == 2 else 0.0
        rewards.append(r)
        grad = np.eye(len(vocab))[action] - probs
        theta += req.learning_rate * req.reward_weight * r * grad
    probs = np.exp(theta) / np.exp(theta).sum()
    return {
        "episode_rewards": rewards,
        "token_distributions": [
            {"token": v, "probability": float(probs[i])}
            for i, v in enumerate(vocab)
        ],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# 2. Frontend
npx create-next-app@latest frontend --use-npm --eslint
cd frontend
npm install recharts
cat > next.config.js << 'EOF'
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/rl/:path*',
        destination: 'http://localhost:8000/api/rl/:path*'
      }
    ]
  }
}
EOF

mkdir -p components pages
cat > components/RLConsole.js << 'EOF'
import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

export default function RLConsole() {
  const [rw, setRw] = useState(1);
  const [lr, setLr] = useState(0.1);
  const [eps, setEps] = useState(10);
  const [data, setData] = useState([]);

  const runSim = async () => {
    const res = await fetch(\`/api/rl/simulate\`, {
      method: 'POST',
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify({ reward_weight: rw, learning_rate: lr, episodes: eps })
    });
    const json = await res.json();
    setData(json.episode_rewards.map((r,i) => ({ episode: i+1, reward: r })));
  };

  return (
    <div>
      <div>
        <label>Reward Weight: <input type="number" value={rw} step="0.1" onChange={e=>setRw(+e.target.value)} /></label>
        <label>Learning Rate: <input type="number" value={lr} step="0.01" onChange={e=>setLr(+e.target.value)} /></label>
        <label>Episodes: <input type="number" value={eps} onChange={e=>setEps(+e.target.value)} /></label>
        <button onClick={runSim}>Run Simulation</button>
      </div>
      <LineChart width={400} height={200} data={data}>
        <XAxis dataKey="episode"/>
        <YAxis/>
        <Tooltip/>
        <Line type="monotone" dataKey="reward"/>
      </LineChart>
    </div>
  );
}
EOF

cat > pages/index.js << 'EOF'
import dynamic from 'next/dynamic';
const RLConsole = dynamic(() => import('../components/RLConsole'), { ssr: false });

export default function Home() {
  return (
    <div className="p-4">
      <h1 className="text-2xl mb-4">Post‑Training RL Explorer</h1>
      <RLConsole />
    </div>
  );
}
EOF

echo "Bootstrap complete! 🔧"
