import type { ErisimDurumu } from "@/lib/api/tipler";

/**
 * Erişim (outreach) durumları — SPEC §3. Kayıt daima `draft` doğar; ileri
 * durumlara **yalnız insan kararıyla** geçilir. Sistem hiçbir koşulda otomatik
 * mesaj göndermez; "sent" bir insanın mesajı elle gönderip işaretlemesidir,
 * arayüzün bir eylemi değildir (CLAUDE.md hukuki sınır).
 *
 * Durum tek bakışta okunur ve renk TEK taşıyıcı değildir: her durum tam adıyla
 * yazılır (renk zaten skora ayrılmış — DESIGN §1).
 */

/** Yaşam döngüsü sırası; select bu sırayla sunar. */
export const ERISIM_SIRA: readonly ErisimDurumu[] = [
  "draft",
  "sent",
  "opened",
  "replied",
  "meeting",
  "won",
  "lost",
];

export const ERISIM_ETIKET: Record<ErisimDurumu, string> = {
  draft: "Taslak",
  sent: "Gönderildi",
  opened: "Açıldı",
  replied: "Yanıtlandı",
  meeting: "Görüşme",
  won: "Kazanıldı",
  lost: "Kaybedildi",
};
