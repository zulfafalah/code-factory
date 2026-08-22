# Kurasi manual adalah gerbang wajib, bukan filter otomatis

Kontenin mengirim video hasil pencarian TikTok ke grup WhatsApp keluarga, dengan
topik yang mencakup pengajian islam dan informasi kesehatan. Setiap
ContentCandidate harus di-approve seorang manusia sebelum bisa dikirim; tidak ada
jalur otomatis apa pun yang bisa melewati gerbang ini.

## Considered Options

`openai` sudah ada di `requirements/base.txt`, jadi filter LLM otomatis adalah
alternatif yang murah dan tersedia. Ditolak: LLM tetap bisa meloloskan potongan
ceramah tanpa konteks atau klaim kesehatan yang keliru, dan penerimanya adalah
orang tua yang mempercayai kiriman ini tanpa punya kebiasaan memverifikasi ulang
di media sosial. Biaya kesalahannya ditanggung mereka, bukan sistem.

Auto-approve saat Ready Pool kosong juga ditolak, dengan alasan yang sama tetapi
lebih tajam: itu akan melonggarkan standar tepat pada saat Curator sedang tidak
memperhatikan.

## Consequences

Ketiadaan Curator menghentikan aliran konten. Itu perilaku yang diinginkan, bukan
kegagalan yang harus ditambal — lihat Skip dan Low Stock Alert di `CONTEXT.md`.

Approval dan kesiapan kirim menjadi dua hal terpisah: Candidate yang sudah
di-approve masih bisa gagal diunduh videonya. Karena itu Ready Pool ada sebagai
konsep tersendiri, bukan sekadar filter `status = approved`.
