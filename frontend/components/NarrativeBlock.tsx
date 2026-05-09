export default function NarrativeBlock({ text }: { text: string }) {
  const paragraphs = text.split(/\n\n+/).filter(Boolean);
  return (
    <div className="space-y-5">
      {paragraphs.map((p, i) => (
        <p key={i} className="text-neutral-400 leading-[1.85] text-[1.05rem]">
          {p.trim()}
        </p>
      ))}
    </div>
  );
}
