# Context

Glosarium istilah domain untuk repo ini. Hanya bahasa domain — tidak ada
detail implementasi, tidak ada keputusan teknis. Keputusan teknis yang sulit
dibalik ditulis sebagai ADR di `docs/adr/`.

## Kontenin

Konteks untuk pipeline kurasi konten: menarik video dari platform sosial,
menyaringnya lewat kurasi manusia, lalu mengantarkannya ke penerima yang tidak
memakai media sosial.

Alasan keberadaannya: penerima hanya memakai WhatsApp. Konten harus datang
kepadanya, bukan sebaliknya.

### Topic

Minat yang ingin diberi makan oleh pipeline — misalnya pertanian, kesehatan,
pengajian islam. Topic adalah istilah domain, bukan istilah pencarian: satu
Topic bisa dicari dengan kata kunci yang berubah-ubah tanpa mengubah Topic-nya.

Topic dikelola oleh Curator dan berubah seiring waktu.

### ContentCandidate

Sebuah video yang telah ditemukan tetapi **belum dinyatakan layak kirim**.

Kata *Candidate* dipilih dengan sengaja. Ditemukannya sebuah video tidak
mengatakan apa pun tentang kelayakannya. Mayoritas Candidate tidak pernah
menjadi Delivery. Jangan menyebutnya "konten" atau "video" tanpa kualifikasi —
istilah itu menyamarkan bahwa barangnya belum lulus kurasi.

Setiap Candidate berasal dari tepat satu Topic.

Panjang video tidak menentukan kelayakan - ceramah panjang sama sahnya dengan
klip satu menit. Yang membatasi adalah ukuran file: video yang tidak muat
sebagai video WhatsApp tidak bisa menjadi Delivery, betapapun layak isinya.

### Curator

Orang yang memutuskan sebuah ContentCandidate layak dikirim. Saat ini satu
orang: pemilik repo ini.

Kurasi bersifat manual dan disengaja. Ketiadaan Curator menghentikan aliran
konten — itu sifat yang diinginkan, bukan kegagalan. Lihat Skip.

### Approval

Tindakan Curator menyatakan sebuah ContentCandidate layak kirim.

Approval **tidak** berarti siap kirim. Sebuah Candidate yang sudah di-approve
masih bisa gagal diambil videonya. Kelayakan (keputusan manusia) dan kesiapan
(video sudah di tangan) adalah dua hal berbeda dan tidak boleh disatukan.

### Ready Pool

Kumpulan Candidate yang sudah di-approve **dan** videonya sudah dimiliki, jadi
benar-benar bisa dikirim. Isinya inilah yang dihitung sebagai "stok".

### Delivery

Satu kiriman video ke Recipient Group pada satu waktu terjadwal.

Satu Delivery membawa satu video. Sebuah video yang sudah pernah menjadi
Delivery tidak dikirim ulang.

### Recipient Group

Percakapan WhatsApp berisi penerima yang dituju. Grup, bukan individu — jadi
kiriman terlihat oleh anggota lain, dan itu membatasi seberapa sering serta
seberapa banyak yang pantas dikirim.

Berbeda dari alamat Curator, yang dipakai untuk peringatan operasional dan
tidak pernah menerima konten kurasi.

### Skip

Jam kirim tiba tetapi Ready Pool kosong, sehingga tidak ada Delivery.

Skip berlangsung senyap terhadap Recipient Group — penerima tidak boleh melihat
pesan kesalahan. Skip bukan hal yang dicegah dengan menurunkan standar kurasi;
Skip dicegah dengan memperingatkan Curator lebih awal.

### Low Stock Alert

Peringatan kepada Curator bahwa Ready Pool akan habis, dikirim saat isinya
turun di bawah ambang.

Peringatan dikirim sebelum kekeringan terjadi, bukan sesudahnya. Tujuannya
memberi Curator waktu untuk mengurasi, bukan memberi tahu bahwa sudah terlambat.
