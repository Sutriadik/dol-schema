# CLAUDE.md

@AGENTS.md

## Tambahan khusus Claude Code

- Perubahan skema adalah keputusan bersama tiga peran. Bila permintaan menyentuh tabel
  `ditunda` atau wilayah RPA/Network, usulkan dulu dalam bentuk catatan di
  `docs/WORKSHOP_SKEMA.md`, jangan langsung mengubah status.
- Setelah `--emit`, uji DDL di PostgreSQL bila tersedia (`psql -f generated/schema.sql` pada
  cluster sementara), bukan hanya tes string.
- Repo ini belum punya remote. Commit & tag boleh bila diminta; push menunggu repo GitHub-nya
  dibuat pengguna.
