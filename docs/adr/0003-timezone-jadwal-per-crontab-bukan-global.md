# Jadwal kirim memakai timezone per-CrontabSchedule; TIME_ZONE global tetap UTC

Penerima Kontenin ada di Indonesia dan jam kirim harus jatuh di waktu WIB, tetapi
`config/settings/base.py` mempertahankan `TIME_ZONE = "UTC"`. Timezone
`Asia/Jakarta` disetel pada `CrontabSchedule` milik jadwal Kontenin saja, lewat
dukungan bawaan `django_celery_beat`.

## Considered Options

Mengubah `TIME_ZONE` global ke `Asia/Jakarta` adalah perubahan satu baris yang
menghilangkan jebakan ini untuk selamanya. Ditolak karena blast radius-nya: repo
ini juga memuat `sales`, `finance`, `ceritain`, `kokorean`, dan `yttoolkit`, yang
sebagian melakukan agregasi harian dengan asumsi batas hari UTC. Menggeser
seluruh proyek tujuh jam demi satu app baru bukan pertukaran yang sepadan.

## Consequences

Seorang pembaca akan melihat proyek untuk penerima Indonesia dengan
`TIME_ZONE = "UTC"` dan mengira itu bug. Bukan — dan mengubahnya berarti
menyentuh app lain yang tidak dites di sini.

Setiap jadwal Kontenin yang dibuat kemudian harus ingat menyetel timezone-nya
sendiri. Jadwal yang lupa disetel akan meleset tujuh jam dan tetap berjalan tanpa
error.
