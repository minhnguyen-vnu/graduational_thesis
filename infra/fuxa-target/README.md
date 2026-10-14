# FUXA, kiểm tay CVE-2026-65984 — 2026-09-28

Image chính thức `frangoteam/fuxa:1.3.2` (bản dính, cổng 1882, container `fuxa-vuln`) và `:1.3.3` (bản vá, cổng
1883, `fuxa-fixed`). Sai lệch đã khai: `settings-secure.js` bật `secureEnabled: true` (một dòng khác
`settings.default-1.3.2.js`). Spec `openapi-1.3.2.yaml` (sha `7d9e9bd24e88392f`) lấy từ tag `v1.3.2`,
`server/docs/openapi.yaml`. Script `handcheck.sh <cổng>`.
