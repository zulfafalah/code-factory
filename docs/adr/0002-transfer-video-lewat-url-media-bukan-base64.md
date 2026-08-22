# Video diserahkan ke OpenWA lewat URL media publik, bukan base64

Gateway WhatsApp-nya adalah **OpenWA** (server `OpenWA API` yang di-host
sendiri, 0.23.x), bukan pustaka npm `open-wa/wa-automate`. Pengiriman dilakukan
lewat `POST /api/sessions/{sessionId}/messages/send-video` dengan header
`X-API-Key`. Endpoint itu menerima `url` atau `base64` + `mimetype`. Kontenin
memakai `url`: mp4 ditulis ke `MEDIA_ROOT`, disajikan nginx lewat
`location /media/`, dan OpenWA yang mengunduhnya.

## Considered Options

Base64 ditolak: mp4 10MB menjadi payload JSON ~13MB per kiriman dan boros
memori di worker. Keunggulannya baru relevan kalau media Django tidak bisa
dijangkau dari luar — lihat Consequences.

Meneruskan URL CDN TikTok langsung tanpa mengunduh juga ditolak: URL itu
kedaluwarsa dalam hitungan jam sementara Candidate diantre berhari-hari
menunggu kurasi, jadi kegagalannya justru terjadi tepat pada jam kirim.

## Consequences

**OpenWA yang menjemput file, bukan Kontenin yang mendorongnya.** URL media
karena itu harus lolos guard outbound milik OpenWA, bukan sekadar bisa
dijangkau Django. Alamat yang ditolak dijawab
`400 {"message":"Destination address is not allowed"}` — pesan yang menyesatkan,
karena terdengar seperti soal nomor tujuan padahal yang ditolak adalah alamat
sumber media. Ini terbukti saat integrasi: satu host contoh publik ditolak
sementara host lain lolos, dan `send-text` ke nomor yang sama tetap berhasil.
Konsekuensi praktisnya: `public_media_base_url` harus alamat publik sungguhan.
Menunjuknya ke hostname internal, IP privat, atau `localhost` akan gagal dengan
pesan itu, dan base64 adalah jalan keluarnya kalau situasi itu terjadi.

**mp4 tersaji di URL tanpa otentikasi.** Ini pilihan sadar, bukan kelalaian:
pengamannya adalah nama file UUID yang tidak bisa ditebak, dan file dihapus tak
lama setelah terkirim. Jangan "memperbaiki" ini dengan menambahkan otentikasi
tanpa lebih dulu pindah ke base64 — OpenWA mengambil file itu sebagai klien
anonim.

**Penghapusan file harus tertunda,** tidak boleh langsung setelah response
kembali: OpenWA mungkin masih di tengah pengunduhan.

**`201` bukan bukti terkirim.** OpenWA menjawab sukses saat pesan diterima
gateway; pengantaran WhatsApp terjadi setelahnya dan bisa gagal diam-diam,
termasuk untuk nomor yang tidak terdaftar. Untuk memastikan nomor ada, pakai
`GET /api/sessions/{sessionId}/contacts/check/{number}` lebih dulu.

**Alamat tujuan harus `@c.us` atau `@g.us`.** Endpoint contact-check
mengembalikan id kanonik berformat `@lid`, tetapi route pengiriman menolaknya
dengan pesan galat yang sama persis. Gateway memetakan `@c.us` ke `@lid`
sendiri.
