"use client";
import { useEffect, useState } from "react";

export default function Game({ params }: { params: { game_id: string } }) {
  const [p, setP] = useState<number | null>(null);
  useEffect(() => {
    const tick = () => fetch(`http://localhost:${process.env.API_PORT || 8000}/game/${params.game_id}/live`).then(r=>r.json()).then(j=>setP(j.p_home));
    tick(); const id = setInterval(tick, 5000); return () => clearInterval(id);
  }, [params.game_id]);
  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold">Game {params.game_id}</h1>
      <div className="mt-4 p-4 bg-slate-800 rounded-xl">Live P(home): {p===null?"...":(p*100).toFixed(1)+"%"}</div>
    </main>
  );
}
