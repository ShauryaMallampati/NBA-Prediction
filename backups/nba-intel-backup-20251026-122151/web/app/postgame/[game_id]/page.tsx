export default function Post({ params }: { params: { game_id: string } }) {
  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold">Postgame {params.game_id}</h1>
      <p className="text-slate-300">Calibration curves and CSV exports will render here.</p>
    </main>
  );
}
