import { ESIK_IZLEMEDE, ESIK_NITELIKLI } from "@/lib/skor";

/**
 * Ray anahtarı — skor sütunu başlığının altında duran sabit ölçek.
 *
 * Rayın 0–100 olduğunu ve 40 / 70 eşiklerinin nerede durduğunu bir kez gösterir,
 * böylece her satırda bant etiketi tekrar etmek gerekmez. Süs değil, ölçeğin
 * kendisi: alet üstündeki kazınmış taksimat.
 */
export function RayAnahtari() {
  return (
    <div
      className="flex flex-col gap-1"
      style={{ width: "var(--olcu-ray-genislik)" }}
    >
      <svg
        viewBox="0 0 100 6"
        preserveAspectRatio="none"
        aria-hidden="true"
        className="w-full"
        height={6}
      >
        <line
          x1={0}
          y1={5}
          x2={100}
          y2={5}
          className="stroke-ray-yol"
          strokeWidth={1}
          vectorEffect="non-scaling-stroke"
        />
        {[ESIK_IZLEMEDE, ESIK_NITELIKLI].map((esik) => (
          <line
            key={esik}
            x1={esik}
            y1={0}
            x2={esik}
            y2={5}
            className="stroke-ray-kohort"
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      <div className="relative h-4">
        <span className="sayi absolute left-0 text-mikro text-metin-2">0</span>
        <span
          className="sayi absolute text-mikro text-metin-2"
          style={{ left: `${ESIK_IZLEMEDE}%`, transform: "translateX(-50%)" }}
        >
          {ESIK_IZLEMEDE}
        </span>
        <span
          className="sayi absolute text-mikro text-metin-2"
          style={{ left: `${ESIK_NITELIKLI}%`, transform: "translateX(-50%)" }}
        >
          {ESIK_NITELIKLI}
        </span>
        <span className="sayi absolute right-0 text-mikro text-metin-2">
          100
        </span>
      </div>
    </div>
  );
}
