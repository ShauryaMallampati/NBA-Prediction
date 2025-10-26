"use client";
import { useEffect, useState } from "react";
import { fetchPredictions } from "./api-proxy";

export default function Home() {
  const [data, setData] = useState<any>(null);
  const date = new Date().toISOString().slice(0,10);
  useEffect(() => { fetchPredictions(date).then(setData).catch(console.error); }, [date]);
  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold mb-4">Schedule — {date}</h1>
      <div className="grid gap-3">
        {data?.games?.length
          ? data.games.map((g: any) => (
              <div key={g.game_id} className="p-4 rounded-xl bg-slate-800">
                <div className="font-semibold">{g.away} at {g.home}</div>
                <div>P(home): {(g.p_home*100).toFixed(1)}%</div>
                <div className="text-sm text-slate-300">Top features: {g.top_features.join(", ")}</div>
              </div>
            ))
          : <div>No games found yet.</div>}
      </div>
    </main>
  );
}
