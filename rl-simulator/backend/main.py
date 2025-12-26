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
