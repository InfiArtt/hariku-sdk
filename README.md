# Hariku Developer SDK

Everything you need to build extensions for [Hariku](https://github.com/InfiArtt/hariku), the
accessible calendar and automation app for Windows, made for blind and low-vision people who
use a screen reader, NVDA first.

[Baca dalam Bahasa Indonesia](#bahasa-indonesia).

## Contents

- [What a Hariku extension is](#what-a-hariku-extension-is)
- [Quick start](#quick-start)
- [Two ways to use the SDK](#two-ways-to-use-the-sdk)
- [What's inside](#whats-inside)
- [Which Hariku version the docs match](#which-hariku-version-the-docs-match)
- [Licensing](#licensing)
- [Submitting to the Extension Store](#submitting-to-the-extension-store)
- [Accessibility expectations](#accessibility-expectations)
- [Help and contributing](#help-and-contributing)
- [Bahasa Indonesia](#bahasa-indonesia)

## What a Hariku extension is

Hariku keeps its core small: most of what it does, from the weather to the world clock, comes
from extensions. An extension is a folder of Python code that Hariku loads when it starts.

- The folder's name is the extension's id, such as `my_tool`.
- `manifest.json` gives its name, version, author, description, entry file, language and the
  oldest Hariku it needs.
- The entry file, usually `main.py`, defines `register(bus)`, which Hariku calls to start the
  extension, and `teardown()`, which Hariku calls when it shuts down.
- The extension talks to Hariku through the `core.*` modules: speech through the user's
  screen reader, keys (every action is also a command for Aruna, Hariku's command bar), pages
  in Preferences, saved data, worker threads, events, reminders and more.
  [DEVELOPERS.md](DEVELOPERS.md) describes all of it.
- It can carry its texts in several languages (`locales/`) and, from Hariku 2.11, a guide for
  its users (`docs/en/guide.md`).
- It is shared as a `.hrk` file, a ZIP made by Hariku's packager, from the Extension Store or
  by hand.

Extensions run with the same rights as Hariku itself; there is no sandbox. That is why the
Extension Store reviews every extension, and why Hariku asks before loading a `.hrk` it
doesn't know.

## Quick start

1. Get the SDK: press **Use this template** at the top of this page to make a repository of
   your own, or download `Hariku_V2_Developer_SDK.zip` from the
   [latest release](https://github.com/InfiArtt/hariku-sdk/releases/latest) and unzip it.
2. Copy `template_extension/`, or the example closest to your idea, to a new folder named
   after your extension's id, in lowercase with underscores: `my_tool`.
3. Edit `manifest.json` (your name, a clear description, a version such as `1.0.0`, and the
   oldest Hariku you need in `minimum_core_version`), then write your code in `main.py`.
4. Check it, then try it: run `python tools/check_extension.py my_tool`, copy the folder into
   `%APPDATA%\Hariku2\extensions\` and restart Hariku. (Or turn on Developer Scratchpad Mode in
   Preferences, Extensions, and point it at your working folder.)
5. Pack it: `python tools/pack.py my_tool` checks it again and writes `dist/my_tool.hrk`.

You need Python 3.10, the Python Hariku runs, for the tools; the tools use nothing but its
standard library.

## Two ways to use the SDK

### Download the SDK ZIP

Every Hariku release gets an SDK release of the same name: `v2.10.0` is the SDK for
Hariku 2.10.0. Download `Hariku_V2_Developer_SDK.zip` from
[the releases page](https://github.com/InfiArtt/hariku-sdk/releases), unzip it, and work in
that folder. It has the guide, the template, the examples, the tools, the store guidelines and
the VS Code settings.

### Start your own repository from the template

This repository is a GitHub template. Press **Use this template**, then **Create a new
repository**, and you get a copy of your own, with a workflow that builds your extension:

1. Copy `template_extension/` to a top-level folder named after your extension's id, and make
   it yours. Every top-level folder with a `manifest.json` counts as an extension.
2. Push. On every push and pull request, `.github/workflows/build-extension.yml` runs
   `tools/check_extension.py` on each extension folder and on `examples/`, and shows any
   problem on the pull request.
3. Tag a release and push the tag, for example `git tag v1.0.0` then `git push origin v1.0.0`.
   The workflow packs each top-level extension folder into a `.hrk` (not `template_extension/`
   or `examples/`) and attaches the files to the GitHub release for that tag, making the
   release if there is none.

In your copy you can delete what you don't need: `examples/`, `store_guidelines/`,
`.github/ISSUE_TEMPLATE/`, `SYNCED_FROM.md`, and `.github/workflows/sync.yml` with
`.github/scripts/`, which only run in this repository.

## What's inside

- `DEVELOPERS.md`: the extension developer guide, the whole API.
- `template_extension/`: "Hello World", the starting point, with a hotkey, a Preferences page,
  a background request and a guide.
- `examples/`: five small, commented extensions, each with English and Indonesian texts and
  guides. See [examples/README.md](examples/README.md).
  - `hello_hotkey`: an action with a default key that speaks, and a double press.
  - `aruna_command`: a shopping list you keep by talking to Aruna, with aliases, and a command
    with content that asks before it saves (Hariku 2.9 or later).
  - `preferences_page`: a page of settings in Preferences, a label before each control.
  - `background_task`: slow work on a worker thread, announced when it's done.
  - `extension_guide`: an extension that ships its own guide and opens it (Hariku 2.11, coming).
- `tools/check_extension.py`: checks an extension folder: the manifest and the rules Hariku's
  loader applies, that every Python file compiles, the language files and their keys, the
  guides, and code the store guidelines warn about (such as `eval()` or `shell=True`). It
  reads your files without running them.
- `tools/pack.py`: checks an extension, then packs it with the packager into `dist/`.
- `tools/packager.py`: Hariku's own packager, which makes `.hrk` files.
- `store_guidelines/`: the Extension Store's submission guide, coding standards, security
  policy and code of conduct.
- `.vscode/`: the VS Code settings from Hariku's own repository; they are meant for a Hariku
  source checkout (their "Run Hariku" starts `hariku.py`).
- `.github/`: the workflows and the issue forms.
- `SYNCED_FROM.md`: which Hariku release and commits the synced files come from.

## Which Hariku version the docs match

- `DEVELOPERS.md`, `tools/packager.py` and `.vscode/` come from the latest Hariku release,
  and a daily workflow brings them up to date. `SYNCED_FROM.md` names the release; today it
  is Hariku 2.10.0.
- `store_guidelines/` comes from Hariku's main branch: the store's rules aren't tied to a
  Hariku version, so the newest ones always apply.
- `template_extension/` comes from Hariku's main branch, so it may already use what the next
  release brings. The template works on Hariku 2.0 and later; its guide shows from 2.11.
- Each example's `minimum_core_version` says the oldest Hariku it runs on. `hello_hotkey`,
  `preferences_page` and `background_task` need 2.0, `aruna_command` 2.9.
- `extension_guide` needs **Hariku 2.11 (coming)**: 2.11 brings extension guides and
  `core.guides`. Until then, Hariku lists it as needing Hariku 2.11 and doesn't load it, and
  the `DEVELOPERS.md` here doesn't describe guides yet; the
  [guide section on Hariku's main branch](https://github.com/InfiArtt/hariku-core/blob/main/DEVELOPERS.md#your-extensions-guide)
  does.
- `DEVELOPERS.md` marks what came later with "core 2.x". Set your own `minimum_core_version`
  to the oldest Hariku that has everything you use.

## Licensing

- The SDK's own files are under the [MIT License](LICENSE): the examples, `tools/check_extension.py`,
  `tools/pack.py`, the tests, the workflows and these pages.
- The template, `template_extension/`, is under the MIT License too, in its own `LICENSE`.
- The files synced from Hariku keep Hariku's license, the GNU GPL version 3 or later with the
  Hariku Extension Exception, and their own license headers: `DEVELOPERS.md`,
  `tools/packager.py`, `store_guidelines/` and `.vscode/`.
- Your extension may use **any license you choose**, open source or proprietary, under the
  [Hariku Extension Exception](https://github.com/InfiArtt/hariku-core/blob/main/LICENSE-EXCEPTION),
  as long as it works with Hariku only through the documented extension API and doesn't copy
  Hariku's own source. Copying the MIT template or examples into it is fine; keep their MIT
  notice with the parts you keep.

[NOTICE.md](NOTICE.md) lists the license of every folder.

## Submitting to the Extension Store

The Extension Store is the list of extensions inside Hariku's Extension Manager. A listed
extension's `.hrk` is registered by its SHA-256, so Hariku installs it without the warning for
unknown extensions. The full rules are in
[store_guidelines/submission_guide.txt](store_guidelines/submission_guide.txt); in short:

### Before you submit

- `manifest.json` has every required field, and `tools/check_extension.py` reports no errors.
  Each update needs a higher version.
- It is packed with the official packager (`tools/pack.py` uses it), not another ZIP tool.
- You tested it on the latest Hariku release, both as an unpacked folder and installed from
  its `.hrk`, with no errors in Hariku's log.
- It has no hardcoded paths, and keeps its data with `core.api.load_data()`,
  `core.api.save_data()` and `core.api.get_storage_dir()`.
- Network and file errors are handled, and the user hears what went wrong.
- It defines `teardown()` and stops its timers and threads there. The store requires it.
- Nothing slow runs on the UI thread: use `core.api.run_thread()`.
- It meets the accessibility expectations below.
- It sends nothing without the user's knowledge, has no tracking or ads, and its code isn't
  hidden or obfuscated.

### How to submit

1. Put your `.hrk` where it can be downloaded, such as the GitHub release your build workflow
   made.
2. Open a [Store submission issue](https://github.com/InfiArtt/hariku-sdk/issues/new?template=store_submission.yml)
   in this repository. The form asks for what the submission guide requires: the `.hrk`, a
   description written for users, a changelog, the Hariku versions, what data the extension
   stores or sends, and a checklist.
3. The review looks at security, whether everything works as described, and accessibility
   with a screen reader. It aims to finish within 7 business days, and ends in approval, a
   request for changes, or a rejection with the reasons.
4. For an update, raise the version, pack again, and submit again with a changelog.

## Accessibility expectations

Hariku's users hear it, and many never see it. Your extension should work the same way.

- **Screen reader first.** Everything works from the keyboard alone, and the user hears what
  happened: say results with `core.speech.speak()`. Don't over-announce, and use
  `interrupt=True` only for what can't wait.
- **Label before control.** Make each `wx.StaticText` label right before the control it
  names. On Windows, NVDA names a text field or a list after the text made just before it;
  make them in another order and every control is read with the wrong name. `SetName()`
  doesn't change what NVDA says. A check box or a button carries its own label.
- A logical Tab order; in dialogs, Enter confirms and Escape cancels.
- Nothing only by color, picture or sound.
- `core.api.main_window_instance` as the parent of your dialogs.
- Nothing slow on the UI thread: a frozen Hariku is a silent Hariku.
- No keyboard hooks. Global keys go through `core.hotkeys`.
- Alerts the user didn't ask for stay quiet during their quiet hours
  (`core.personal.is_quiet_time()`, Hariku 2.7).
- A guide with a heading for each task, so screen reader users can jump to it.
- Test with a screen reader before you submit. NVDA is free.

## Help and contributing

- A problem in the SDK or its docs: open a
  [bug report](https://github.com/InfiArtt/hariku-sdk/issues/new?template=bug_report.yml).
- A problem in the Hariku app: [Hariku's issues](https://github.com/InfiArtt/hariku/issues).
- A security problem: report it privately, as
  [store_guidelines/security_policy.txt](store_guidelines/security_policy.txt) describes.
- To improve the SDK, read [CONTRIBUTING.md](CONTRIBUTING.md). The synced files are changed
  in [Hariku's source](https://github.com/InfiArtt/hariku-core).

---

## Bahasa Indonesia

Semua yang kamu perlukan untuk membuat ekstensi bagi [Hariku](https://github.com/InfiArtt/hariku),
aplikasi kalender dan otomatisasi yang aksesibel untuk Windows, dibuat untuk tunanetra dan
orang dengan low vision yang memakai pembaca layar, terutama NVDA.

### Isi

- [Apa itu ekstensi Hariku](#apa-itu-ekstensi-hariku)
- [Mulai cepat](#mulai-cepat)
- [Dua cara memakai SDK](#dua-cara-memakai-sdk)
- [Isi SDK](#isi-sdk)
- [Versi Hariku yang dicakup dokumentasi](#versi-hariku-yang-dicakup-dokumentasi)
- [Lisensi](#lisensi)
- [Mengirim ke Toko Ekstensi](#mengirim-ke-toko-ekstensi)
- [Harapan soal aksesibilitas](#harapan-soal-aksesibilitas)
- [Bantuan dan kontribusi](#bantuan-dan-kontribusi)

### Apa itu ekstensi Hariku

Inti Hariku dibuat kecil: sebagian besar fiturnya, dari cuaca sampai jam dunia, datang dari
ekstensi. Ekstensi adalah folder berisi kode Python yang dimuat Hariku saat mulai.

- Nama foldernya adalah id ekstensi, misalnya `my_tool`.
- `manifest.json` berisi nama, versi, pembuat, deskripsi, file utama, bahasa, dan versi Hariku
  tertua yang dibutuhkan.
- File utamanya, biasanya `main.py`, mendefinisikan `register(bus)`, yang dipanggil Hariku
  untuk menjalankan ekstensi, dan `teardown()`, yang dipanggil Hariku saat ditutup.
- Ekstensi berbicara dengan Hariku lewat modul `core.*`: suara lewat pembaca layar pengguna,
  tombol pintasan (setiap aksi juga menjadi perintah untuk Aruna, bilah perintah Hariku),
  halaman di Pengaturan, data tersimpan, thread pekerja, event, pengingat, dan lain-lain.
  [DEVELOPERS.md](DEVELOPERS.md) menjelaskan semuanya (dalam bahasa Inggris).
- Ekstensi bisa membawa teksnya dalam beberapa bahasa (`locales/`) dan, mulai Hariku 2.11,
  panduan untuk penggunanya (`docs/id/guide.md`, `docs/en/guide.md`).
- Ekstensi dibagikan sebagai file `.hrk`, yaitu ZIP buatan packager Hariku, lewat Toko
  Ekstensi atau secara manual.

Ekstensi berjalan dengan hak yang sama seperti Hariku sendiri; tidak ada sandbox. Karena itu
Toko Ekstensi memeriksa setiap ekstensi, dan Hariku bertanya dulu sebelum memuat `.hrk` yang
belum dikenalnya.

### Mulai cepat

1. Ambil SDK-nya: tekan **Use this template** di bagian atas halaman ini untuk membuat
   repositori milikmu sendiri, atau unduh `Hariku_V2_Developer_SDK.zip` dari
   [rilis terbaru](https://github.com/InfiArtt/hariku-sdk/releases/latest) lalu ekstrak.
2. Salin `template_extension/`, atau contoh yang paling dekat dengan idemu, ke folder baru
   bernama id ekstensimu, huruf kecil dengan garis bawah: `my_tool`.
3. Ubah `manifest.json` (namamu, deskripsi yang jelas, versi seperti `1.0.0`, dan versi Hariku
   tertua yang kamu butuhkan di `minimum_core_version`), lalu tulis kodemu di `main.py`.
4. Periksa, lalu coba: jalankan `python tools/check_extension.py my_tool`, salin foldernya ke
   `%APPDATA%\Hariku2\extensions\`, dan mulai ulang Hariku. (Atau nyalakan Developer
   Scratchpad Mode di Pengaturan, Extensions, dan arahkan ke folder kerjamu.)
5. Kemas: `python tools/pack.py my_tool` memeriksanya lagi dan menulis `dist/my_tool.hrk`.

Untuk menjalankan alat-alatnya kamu butuh Python 3.10, versi Python yang dipakai Hariku;
alat-alatnya hanya memakai pustaka standar Python.

### Dua cara memakai SDK

#### Unduh ZIP SDK

Setiap rilis Hariku mendapat rilis SDK dengan nama yang sama: `v2.10.0` adalah SDK untuk
Hariku 2.10.0. Unduh `Hariku_V2_Developer_SDK.zip` dari
[halaman rilis](https://github.com/InfiArtt/hariku-sdk/releases), ekstrak, lalu bekerja di
folder itu. Isinya panduan, template, contoh, alat, pedoman toko, dan pengaturan VS Code.

#### Mulai repositorimu sendiri dari template

Repositori ini adalah template GitHub. Tekan **Use this template**, lalu **Create a new
repository**, dan kamu mendapat salinan milikmu sendiri, lengkap dengan workflow yang
membangun ekstensimu:

1. Salin `template_extension/` ke folder di tingkat teratas yang bernama id ekstensimu, lalu
   jadikan milikmu. Setiap folder tingkat teratas yang punya `manifest.json` dianggap ekstensi.
2. Push. Di setiap push dan pull request, `.github/workflows/build-extension.yml` menjalankan
   `tools/check_extension.py` pada setiap folder ekstensi dan pada `examples/`, lalu
   menunjukkan masalahnya di pull request.
3. Beri tag rilis lalu push tag-nya, misalnya `git tag v1.0.0` lalu `git push origin v1.0.0`.
   Workflow-nya mengemas setiap folder ekstensi tingkat teratas menjadi `.hrk` (kecuali
   `template_extension/` dan `examples/`) dan melampirkannya ke rilis GitHub untuk tag itu,
   sekaligus membuat rilisnya kalau belum ada.

Di salinanmu, kamu boleh menghapus yang tidak kamu perlukan: `examples/`, `store_guidelines/`,
`.github/ISSUE_TEMPLATE/`, `SYNCED_FROM.md`, serta `.github/workflows/sync.yml` bersama
`.github/scripts/`, yang hanya berjalan di repositori ini.

### Isi SDK

- `DEVELOPERS.md`: panduan pengembang ekstensi, seluruh API-nya.
- `template_extension/`: "Hello World", titik awalnya, dengan tombol pintasan, halaman
  Pengaturan, permintaan di latar belakang, dan panduan.
- `examples/`: lima ekstensi kecil yang diberi komentar, masing-masing dengan teks dan panduan
  berbahasa Inggris dan Indonesia. Lihat [examples/README.md](examples/README.md).
  - `hello_hotkey`: aksi dengan tombol bawaan yang berbicara, dan tekan dua kali.
  - `aruna_command`: daftar belanja yang kamu isi dengan berbicara ke Aruna, dengan alias,
    dan perintah berisi yang bertanya dulu sebelum menyimpan (Hariku 2.9 atau lebih baru).
  - `preferences_page`: halaman pengaturan di Pengaturan, dengan label sebelum setiap kontrol.
  - `background_task`: pekerjaan lambat di thread pekerja, diumumkan saat selesai.
  - `extension_guide`: ekstensi yang membawa panduannya sendiri dan membukanya (Hariku 2.11,
    segera hadir).
- `tools/check_extension.py`: memeriksa folder ekstensi: manifest dan aturan pemuat ekstensi
  Hariku, apakah setiap file Python bisa dikompilasi, file bahasa dan kuncinya, panduan, dan
  kode yang diperingatkan pedoman toko (seperti `eval()` atau `shell=True`). Ia membaca
  file-filemu tanpa menjalankannya.
- `tools/pack.py`: memeriksa ekstensi, lalu mengemasnya dengan packager ke `dist/`.
- `tools/packager.py`: packager milik Hariku, yang membuat file `.hrk`.
- `store_guidelines/`: panduan pengiriman Toko Ekstensi, standar kode, kebijakan keamanan, dan
  kode etik (dalam bahasa Inggris).
- `.vscode/`: pengaturan VS Code dari repositori Hariku; dibuat untuk salinan kode sumber
  Hariku ("Run Hariku" menjalankan `hariku.py`).
- `.github/`: workflow dan formulir issue.
- `SYNCED_FROM.md`: rilis dan commit Hariku asal file-file yang disinkronkan.

### Versi Hariku yang dicakup dokumentasi

- `DEVELOPERS.md`, `tools/packager.py`, dan `.vscode/` diambil dari rilis Hariku terbaru, dan
  workflow harian memperbaruinya. `SYNCED_FROM.md` menyebut rilisnya; saat ini Hariku 2.10.0.
- `store_guidelines/` diambil dari cabang main Hariku: aturan toko tidak terikat pada versi
  Hariku, jadi yang terbaru selalu berlaku.
- `template_extension/` diambil dari cabang main Hariku, jadi mungkin sudah memakai yang dibawa
  rilis berikutnya. Template-nya berjalan di Hariku 2.0 ke atas; panduannya tampil mulai 2.11.
- `minimum_core_version` di setiap contoh menyebut versi Hariku tertua yang bisa
  menjalankannya. `hello_hotkey`, `preferences_page`, dan `background_task` butuh 2.0,
  `aruna_command` 2.9.
- `extension_guide` butuh **Hariku 2.11 (segera hadir)**: 2.11 membawa panduan ekstensi dan
  `core.guides`. Sampai saat itu, Hariku mencantumkannya sebagai butuh Hariku 2.11 dan tidak
  memuatnya, dan `DEVELOPERS.md` di sini belum menjelaskan panduan; bagian
  [panduan di cabang main Hariku](https://github.com/InfiArtt/hariku-core/blob/main/DEVELOPERS.md#your-extensions-guide)
  sudah.
- `DEVELOPERS.md` menandai fitur yang datang belakangan dengan "core 2.x". Isi
  `minimum_core_version` milikmu dengan versi Hariku tertua yang punya semua yang kamu pakai.

### Lisensi

- File milik SDK sendiri memakai [Lisensi MIT](LICENSE): contoh, `tools/check_extension.py`,
  `tools/pack.py`, pengujian, workflow, dan halaman-halaman ini.
- Template-nya, `template_extension/`, juga memakai Lisensi MIT, di `LICENSE`-nya sendiri.
- File yang disinkronkan dari Hariku tetap memakai lisensi Hariku, GNU GPL versi 3 atau yang
  lebih baru dengan Hariku Extension Exception, beserta header lisensinya sendiri:
  `DEVELOPERS.md`, `tools/packager.py`, `store_guidelines/`, dan `.vscode/`.
- Ekstensimu boleh memakai **lisensi apa pun yang kamu pilih**, open source maupun
  proprietary, berdasarkan
  [Hariku Extension Exception](https://github.com/InfiArtt/hariku-core/blob/main/LICENSE-EXCEPTION),
  selama ekstensimu berhubungan dengan Hariku hanya lewat API ekstensi yang terdokumentasi dan
  tidak menyalin kode sumber Hariku sendiri. Menyalin template atau contoh ber-MIT ke dalamnya
  boleh; sertakan pemberitahuan MIT-nya bersama bagian yang kamu pertahankan.

[NOTICE.md](NOTICE.md) mencantumkan lisensi setiap folder.

### Mengirim ke Toko Ekstensi

Toko Ekstensi adalah daftar ekstensi di dalam Pengelola Ekstensi Hariku. File `.hrk` ekstensi
yang terdaftar dicatat SHA-256-nya, jadi Hariku memasangnya tanpa peringatan untuk ekstensi
yang tidak dikenal. Aturan lengkapnya ada di
[store_guidelines/submission_guide.txt](store_guidelines/submission_guide.txt); ringkasnya:

#### Sebelum mengirim

- `manifest.json` punya semua kolom wajib, dan `tools/check_extension.py` tidak melaporkan
  error. Setiap pembaruan butuh versi yang lebih tinggi.
- Dikemas dengan packager resmi (`tools/pack.py` memakainya), bukan alat ZIP lain.
- Kamu sudah mengujinya di rilis Hariku terbaru, sebagai folder yang belum dikemas dan setelah
  dipasang dari `.hrk`-nya, tanpa error di log Hariku.
- Tidak ada path yang ditulis mati, dan datanya disimpan dengan `core.api.load_data()`,
  `core.api.save_data()`, dan `core.api.get_storage_dir()`.
- Error jaringan dan file ditangani, dan pengguna mendengar apa yang salah.
- Mendefinisikan `teardown()` dan menghentikan timer serta thread-nya di sana. Toko
  mewajibkannya.
- Tidak ada pekerjaan lambat di thread UI: pakai `core.api.run_thread()`.
- Memenuhi harapan aksesibilitas di bawah.
- Tidak mengirim apa pun tanpa sepengetahuan pengguna, tanpa pelacakan atau iklan, dan kodenya
  tidak disembunyikan atau diacak.

#### Cara mengirim

1. Taruh `.hrk`-mu di tempat yang bisa diunduh, misalnya rilis GitHub yang dibuat workflow
   build-mu.
2. Buka [issue Store submission](https://github.com/InfiArtt/hariku-sdk/issues/new?template=store_submission.yml)
   di repositori ini. Formulirnya meminta yang diwajibkan panduan pengiriman: `.hrk`,
   deskripsi yang ditulis untuk pengguna, changelog, versi Hariku, data apa yang disimpan atau
   dikirim ekstensinya, dan daftar periksa.
3. Pemeriksaan mencakup keamanan, apakah semuanya bekerja seperti yang dijelaskan, dan
   aksesibilitas dengan pembaca layar. Targetnya selesai dalam 7 hari kerja, dengan hasil
   disetujui, diminta perbaikan, atau ditolak beserta alasannya.
4. Untuk pembaruan, naikkan versinya, kemas lagi, dan kirim lagi dengan changelog.

### Harapan soal aksesibilitas

Pengguna Hariku mendengarnya, dan banyak yang tidak pernah melihatnya. Ekstensimu sebaiknya
bekerja dengan cara yang sama.

- **Pembaca layar yang utama.** Semuanya bisa dilakukan dengan keyboard saja, dan pengguna
  mendengar apa yang terjadi: ucapkan hasilnya dengan `core.speech.speak()`. Jangan terlalu
  banyak bicara, dan pakai `interrupt=True` hanya untuk yang tidak bisa menunggu.
- **Label sebelum kontrol.** Buat setiap label `wx.StaticText` tepat sebelum kontrol yang
  dinamainya. Di Windows, NVDA menamai kolom teks atau daftar dengan teks yang dibuat tepat
  sebelumnya; kalau urutannya lain, setiap kontrol dibacakan dengan nama yang salah.
  `SetName()` tidak mengubah yang diucapkan NVDA. Kotak centang dan tombol membawa labelnya
  sendiri.
- Urutan Tab yang masuk akal; di dialog, Enter mengonfirmasi dan Escape membatalkan.
- Tidak ada informasi yang hanya lewat warna, gambar, atau suara.
- `core.api.main_window_instance` sebagai induk dialog-dialogmu.
- Tidak ada pekerjaan lambat di thread UI: Hariku yang membeku adalah Hariku yang diam.
- Tidak ada keyboard hook. Tombol global lewat `core.hotkeys`.
- Peringatan yang tidak diminta pengguna tetap diam selama jam tenangnya
  (`core.personal.is_quiet_time()`, Hariku 2.7).
- Panduan dengan judul bagian untuk setiap tugas, supaya pengguna pembaca layar bisa langsung
  melompat ke sana.
- Uji dengan pembaca layar sebelum mengirim. NVDA gratis.

### Bantuan dan kontribusi

- Masalah di SDK atau dokumentasinya: buka
  [laporan bug](https://github.com/InfiArtt/hariku-sdk/issues/new?template=bug_report.yml).
- Masalah di aplikasi Hariku: [issue Hariku](https://github.com/InfiArtt/hariku/issues).
- Masalah keamanan: laporkan secara pribadi, seperti yang dijelaskan
  [store_guidelines/security_policy.txt](store_guidelines/security_policy.txt).
- Untuk memperbaiki SDK, baca [CONTRIBUTING.md](CONTRIBUTING.md). File yang disinkronkan diubah
  di [kode sumber Hariku](https://github.com/InfiArtt/hariku-core).
