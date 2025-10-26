export async function fetchPredictions(date: string) {
  const url = `http://localhost:${process.env.API_PORT || 8000}/predictions?date=${date}`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("API error");
  return res.json();
}
